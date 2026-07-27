# Copyright (c) Microsoft. All rights reserved.

import hashlib
import json
import logging
import math
import time
import uuid
from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import Field

from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
        AutoFunctionInvocationContext,
    )

logger = logging.getLogger(__name__)

RISK_LEVEL_PROPERTY = "risk_level"
REQUIRES_APPROVAL_PROPERTY = "requires_approval"


@experimental
class FunctionRiskLevel(str, Enum):
    """Risk classification for a kernel function used by the authorization filter."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_RISK_ORDER = {
    FunctionRiskLevel.LOW: 0,
    FunctionRiskLevel.MEDIUM: 1,
    FunctionRiskLevel.HIGH: 2,
    FunctionRiskLevel.CRITICAL: 3,
}


@experimental
class FunctionAuthorizationAction(str, Enum):
    """Terminal authorization action for a proposed auto function invocation."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@experimental
class FunctionAuthorizationStatus(str, Enum):
    """Lifecycle status of an authorization decision, recorded in the audit log."""

    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    EXECUTED = "executed"
    FAILED = "failed"


@experimental
class FunctionAuthorizationDecision(KernelBaseModel):
    """An explicit, auditable record of a single authorization decision.

    The decision binds the outcome to the exact call that was proposed:
    the fully qualified function name, a canonical digest of the arguments,
    the principal on whose behalf the call runs and a digest of the policy
    that produced the decision. An approval is only valid for the identical
    binding, so changing any of these invalidates it.
    """

    decision_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    function_name: str
    args_digest: str
    principal: str
    policy_digest: str
    risk: FunctionRiskLevel
    action: FunctionAuthorizationAction
    status: FunctionAuthorizationStatus
    reason: str
    authority_source: str
    created_at: float = Field(default_factory=time.time)

    @property
    def binding(self) -> str:
        """The tag an approval must match for this exact call to be dispatched."""
        material = "|".join([self.function_name, self.args_digest, self.principal, self.policy_digest])
        return hashlib.sha256(material.encode("utf-8")).hexdigest()


@experimental
class FunctionApprovalStore:
    """In-memory, single-use store of granted approvals keyed by decision binding.

    Approvals expire after a time-to-live and are consumed on use, so a granted
    approval authorizes at most one dispatch of the exact call it was bound to.
    Replace with a durable implementation for multi-process scenarios.
    """

    def __init__(self) -> None:
        """Initialize an empty approval store."""
        self._approvals: dict[str, float] = {}

    def grant(self, binding: str, ttl_seconds: float) -> None:
        """Grant a single-use approval for the given decision binding.

        Raises:
            ValueError: If ``ttl_seconds`` is not a finite, positive number,
                which would otherwise create an approval that never expires.
        """
        if not math.isfinite(ttl_seconds) or ttl_seconds <= 0:
            raise ValueError(f"ttl_seconds must be a finite, positive number, got {ttl_seconds!r}.")
        self._approvals[binding] = time.time() + ttl_seconds

    def consume(self, binding: str) -> str:
        """Consume an approval for the binding; returns 'ok', 'expired' or 'absent'."""
        expires_at = self._approvals.pop(binding, None)
        if expires_at is None:
            return "absent"
        if time.time() > expires_at:
            return "expired"
        return "ok"


@experimental
class FunctionAuthorizationPolicy(KernelBaseModel):
    """Declarative, deterministic policy evaluated before every auto function invocation.

    Risk resolution is fail-closed: a function with no declared risk is treated as
    ``default_risk`` (HIGH unless configured otherwise), and the most restrictive
    signal wins between declared risk and the keyword guard.

    Args:
        risk_overrides: Map of fully qualified function name (``plugin-function``)
            or plugin wildcard (``plugin-*``) to a risk level. Exact names win
            over wildcards.
        keyword_guard: Case-insensitive substrings that escalate the resolved
            risk to at least the mapped level when found in the rendered
            arguments. This is a deterministic tripwire for indirect prompt
            injection payloads, not a semantic classifier.
        action_map: Terminal action per risk level. Defaults to ALLOW for
            LOW/MEDIUM, REQUIRE_APPROVAL for HIGH and DENY for CRITICAL.
        default_risk: Risk assigned to functions with no declared classification.
        principal: Identifier of the caller/session the decisions are bound to.
        approval_ttl_seconds: Lifetime of a granted approval.
        terminate_on_pending: Whether a pending approval also terminates the
            auto-invocation loop so the pending decision surfaces to the caller.
    """

    risk_overrides: dict[str, FunctionRiskLevel] = Field(default_factory=dict)
    keyword_guard: dict[str, FunctionRiskLevel] = Field(default_factory=dict)
    action_map: dict[FunctionRiskLevel, FunctionAuthorizationAction] = Field(
        default_factory=lambda: {
            FunctionRiskLevel.LOW: FunctionAuthorizationAction.ALLOW,
            FunctionRiskLevel.MEDIUM: FunctionAuthorizationAction.ALLOW,
            FunctionRiskLevel.HIGH: FunctionAuthorizationAction.REQUIRE_APPROVAL,
            FunctionRiskLevel.CRITICAL: FunctionAuthorizationAction.DENY,
        }
    )
    default_risk: FunctionRiskLevel = FunctionRiskLevel.HIGH
    principal: str = "default"
    approval_ttl_seconds: float = 300.0
    terminate_on_pending: bool = True

    @property
    def policy_digest(self) -> str:
        """A digest of the policy, so approvals are invalidated by policy changes."""
        snapshot = json.dumps(
            {
                "risk_overrides": {k: v.value for k, v in sorted(self.risk_overrides.items())},
                "keyword_guard": {k: v.value for k, v in sorted(self.keyword_guard.items())},
                "action_map": {k.value: v.value for k, v in sorted(self.action_map.items())},
                "default_risk": self.default_risk.value,
                "principal": self.principal,
            },
            sort_keys=True,
        )
        return hashlib.sha256(snapshot.encode("utf-8")).hexdigest()

    def resolve_risk(
        self,
        fully_qualified_name: str,
        plugin_name: str | None,
        additional_properties: Mapping[str, Any] | None,
        rendered_arguments: str,
    ) -> tuple[FunctionRiskLevel, str, bool]:
        """Resolve the risk for a proposed call; returns (risk, reason, requires_approval).

        Precedence: exact policy override > plugin wildcard override > function
        metadata (``additional_properties``) > ``default_risk`` (fail-closed).
        The keyword guard can only escalate the resolved risk, never lower it.
        """
        requires_approval = False
        if fully_qualified_name in self.risk_overrides:
            risk = self.risk_overrides[fully_qualified_name]
            reason = f"policy override for '{fully_qualified_name}'"
        elif plugin_name and f"{plugin_name}-*" in self.risk_overrides:
            risk = self.risk_overrides[f"{plugin_name}-*"]
            reason = f"policy override for plugin '{plugin_name}'"
        else:
            declared = (additional_properties or {}).get(RISK_LEVEL_PROPERTY)
            if declared is not None:
                try:
                    risk = FunctionRiskLevel(str(declared).lower())
                    reason = f"declared {RISK_LEVEL_PROPERTY}='{risk.value}' in function metadata"
                except ValueError:
                    risk = self.default_risk
                    reason = (
                        f"invalid {RISK_LEVEL_PROPERTY} '{declared}' in function metadata, "
                        f"failing closed to default risk '{risk.value}'"
                    )
            else:
                risk = self.default_risk
                reason = f"no declared risk, failing closed to default risk '{risk.value}'"
        if (additional_properties or {}).get(REQUIRES_APPROVAL_PROPERTY):
            requires_approval = True
        haystack = rendered_arguments.lower()
        for keyword, guard_risk in self.keyword_guard.items():
            if keyword.lower() in haystack and _RISK_ORDER[guard_risk] > _RISK_ORDER[risk]:
                risk = guard_risk
                reason = f"keyword guard matched '{keyword}', escalating to '{risk.value}'"
        return risk, reason, requires_approval

    def action_for(self, risk: FunctionRiskLevel, requires_approval: bool) -> FunctionAuthorizationAction:
        """Map resolved risk to a terminal action; unmapped risk levels fail closed to DENY."""
        action = self.action_map.get(risk, FunctionAuthorizationAction.DENY)
        if requires_approval and action == FunctionAuthorizationAction.ALLOW:
            return FunctionAuthorizationAction.REQUIRE_APPROVAL
        return action


@experimental
class FunctionAuthorizationFilter:
    """An AUTO_FUNCTION_INVOCATION filter that turns function dispatch into an authorized action.

    Register it like any other filter::

        kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, auth_filter)

    For every function call proposed by the model, the filter deterministically
    resolves a risk level and records an explicit :class:`FunctionAuthorizationDecision`:

    - ALLOW: the call is dispatched (``await next(context)``).
    - DENY: the call is never dispatched; the model receives a structured refusal.
    - REQUIRE_APPROVAL: the call is never dispatched; a pending decision is
      surfaced as the function result (and, by default, terminates the
      auto-invocation loop). After :meth:`grant_approval`, re-invoking the same
      call — same function, same canonical arguments, same principal, same
      policy — dispatches it exactly once.

    Because approvals are bound to the canonical argument digest, an approval
    granted for ``transfer(amount=10)`` can never be replayed for
    ``transfer(amount=10000)``, closing the time-of-check/time-of-use gap.
    Prompt injection can therefore make the model *propose* a call, but never
    bypass the checkpoint that dispatches it.

    Notes:
        - Filters form a chain and the most recently added filter runs
          innermost. Add this filter *last*, so no other filter runs (and can
          mutate the arguments) between the authorization check and dispatch.
        - Filters are trusted application code. The boundary enforced here is
          between untrusted model output and dispatch, not between filters.
        - EXECUTED means the call was dispatched; if dispatch raises, the
          decision is recorded as FAILED and the exception propagates.
        - Arguments that cannot be canonicalized fail closed to DENY.
    """

    def __init__(
        self,
        policy: FunctionAuthorizationPolicy | None = None,
        approval_store: FunctionApprovalStore | None = None,
    ) -> None:
        """Initialize the filter with an optional policy and approval store."""
        self.policy = policy or FunctionAuthorizationPolicy()
        self.approvals = approval_store or FunctionApprovalStore()
        self.audit_log: list[FunctionAuthorizationDecision] = []
        self._ordering_warned = False

    @classmethod
    def render_canonical_arguments(cls, arguments: Mapping[str, Any] | None) -> str:
        """Render the call arguments to a canonical, order-independent string.

        Every value is encoded together with a structural type tag, so values
        of different types can never render identically: a native string can
        never collide with an object whose ``__str__`` (or type-prefixed
        rendering) mimics it, because their tags differ.

        Any failure to canonicalize (for example, a circular reference) raises,
        and callers must treat it as fail-closed.
        """
        return json.dumps(cls._canonicalize(dict(arguments or {})), sort_keys=True, separators=(",", ":"))

    @classmethod
    def _canonicalize(cls, value: Any) -> Any:
        """Recursively encode a value with structural type tags."""
        if value is None:
            return ["null"]
        if isinstance(value, bool):
            return ["bool", value]
        if isinstance(value, int):
            return ["int", value]
        if isinstance(value, float):
            return ["float", repr(value)]
        if isinstance(value, str):
            return ["str", value]
        if isinstance(value, Mapping):
            items = [[cls._canonicalize(key), cls._canonicalize(item)] for key, item in value.items()]
            return ["map", sorted(items, key=lambda pair: json.dumps(pair, sort_keys=True))]
        if isinstance(value, (list, tuple)):
            return ["seq", [cls._canonicalize(item) for item in value]]
        value_type = type(value)
        return ["obj", f"{value_type.__module__}.{value_type.__qualname__}", str(value)]

    @classmethod
    def canonical_args_digest(cls, arguments: Mapping[str, Any] | None) -> str:
        """Compute an order-independent digest of the call arguments."""
        rendered = cls.render_canonical_arguments(arguments)
        return hashlib.sha256(rendered.encode("utf-8")).hexdigest()

    def grant_approval(self, decision: FunctionAuthorizationDecision, ttl_seconds: float | None = None) -> None:
        """Grant a single-use approval for the exact call recorded in the decision."""
        self.approvals.grant(
            decision.binding, ttl_seconds if ttl_seconds is not None else self.policy.approval_ttl_seconds
        )

    async def __call__(self, context: "AutoFunctionInvocationContext", next) -> None:
        """Authorize the proposed function call before it is dispatched."""
        registered_filters = getattr(context.kernel, "auto_function_invocation_filters", None)
        if registered_filters and registered_filters[0][1] is not self and not self._ordering_warned:
            self._ordering_warned = True
            logger.warning(
                "FunctionAuthorizationFilter is not the innermost AUTO_FUNCTION_INVOCATION filter: "
                "filters registered after it run between the authorization check and dispatch and "
                "could alter the authorized call. Register this filter last to close that gap."
            )
        function_name = context.function.fully_qualified_name
        arguments = dict(context.arguments or {})
        try:
            rendered_arguments = self.render_canonical_arguments(arguments)
        except Exception:
            # Arguments that cannot be canonicalized (circular references,
            # hostile __str__ implementations, ...) fail closed: the call is
            # denied and audited rather than dispatched or crashing the gate.
            decision = FunctionAuthorizationDecision(
                function_name=function_name,
                args_digest="uncanonicalizable",
                principal=self.policy.principal,
                policy_digest=self.policy.policy_digest,
                risk=FunctionRiskLevel.CRITICAL,
                action=FunctionAuthorizationAction.DENY,
                status=FunctionAuthorizationStatus.DENIED,
                reason="arguments could not be canonicalized, failing closed",
                authority_source="policy",
            )
            self.audit_log.append(decision)
            logger.warning("Function '%s' denied: %s", function_name, decision.reason)
            context.function_result = FunctionResult(
                function=context.function.metadata,
                value={
                    "authorization": "denied",
                    "decision_id": decision.decision_id,
                    "function": function_name,
                    "reason": decision.reason,
                    "message": (
                        f"The call to '{function_name}' was blocked by the function authorization "
                        "policy and was not executed."
                    ),
                },
            )
            return
        args_digest = hashlib.sha256(rendered_arguments.encode("utf-8")).hexdigest()
        risk, reason, requires_approval = self.policy.resolve_risk(
            function_name,
            context.function.plugin_name,
            context.function.metadata.additional_properties,
            rendered_arguments,
        )
        decision = FunctionAuthorizationDecision(
            function_name=function_name,
            args_digest=args_digest,
            principal=self.policy.principal,
            policy_digest=self.policy.policy_digest,
            risk=risk,
            action=self.policy.action_for(risk, requires_approval),
            status=FunctionAuthorizationStatus.PENDING_APPROVAL,
            reason=reason,
            authority_source="policy",
        )
        self.audit_log.append(decision)

        if decision.action != FunctionAuthorizationAction.ALLOW:
            approval = self.approvals.consume(decision.binding)
            if approval == "ok" and decision.action == FunctionAuthorizationAction.REQUIRE_APPROVAL:
                decision.action = FunctionAuthorizationAction.ALLOW
                decision.authority_source = "user_approval"
                decision.status = FunctionAuthorizationStatus.APPROVED
                decision.reason = f"approved by '{self.policy.principal}' for this exact call ({reason})"
            elif approval == "expired":
                decision.status = FunctionAuthorizationStatus.EXPIRED
                decision.reason = f"approval expired before dispatch ({reason})"

        if decision.action == FunctionAuthorizationAction.ALLOW:
            if decision.status != FunctionAuthorizationStatus.APPROVED:
                decision.status = FunctionAuthorizationStatus.APPROVED
            logger.debug("Function '%s' authorized: %s", function_name, decision.reason)
            try:
                await next(context)
            except Exception:
                decision.status = FunctionAuthorizationStatus.FAILED
                raise
            decision.status = FunctionAuthorizationStatus.EXECUTED
            return

        if decision.action == FunctionAuthorizationAction.DENY:
            decision.status = FunctionAuthorizationStatus.DENIED
            logger.warning("Function '%s' denied: %s", function_name, decision.reason)
            context.function_result = FunctionResult(
                function=context.function.metadata,
                value={
                    "authorization": "denied",
                    "decision_id": decision.decision_id,
                    "function": function_name,
                    "reason": decision.reason,
                    "message": (
                        f"The call to '{function_name}' was blocked by the function authorization "
                        "policy and was not executed."
                    ),
                },
            )
            return

        if decision.status != FunctionAuthorizationStatus.EXPIRED:
            decision.status = FunctionAuthorizationStatus.PENDING_APPROVAL
        logger.warning("Function '%s' requires approval: %s", function_name, decision.reason)
        context.function_result = FunctionResult(
            function=context.function.metadata,
            value={
                "authorization": "pending_approval",
                "decision_id": decision.decision_id,
                "function": function_name,
                "args_digest": decision.args_digest,
                "reason": decision.reason,
                "message": (
                    f"The call to '{function_name}' was suspended pending approval and was not "
                    "executed. A caller with authority can grant the approval and re-issue the "
                    "identical call."
                ),
            },
        )
        if self.policy.terminate_on_pending:
            context.terminate = True


__all__ = [
    "REQUIRES_APPROVAL_PROPERTY",
    "RISK_LEVEL_PROPERTY",
    "FunctionApprovalStore",
    "FunctionAuthorizationAction",
    "FunctionAuthorizationDecision",
    "FunctionAuthorizationFilter",
    "FunctionAuthorizationPolicy",
    "FunctionAuthorizationStatus",
    "FunctionRiskLevel",
]
