# Copyright (c) Microsoft. All rights reserved.

import time

from pytest import fixture, raises

from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.filters import (
    FilterTypes,
    FunctionAuthorizationAction,
    FunctionAuthorizationFilter,
    FunctionAuthorizationPolicy,
    FunctionAuthorizationStatus,
    FunctionRiskLevel,
)
from semantic_kernel.filters.auto_function_invocation.function_authorization_filter import (
    REQUIRES_APPROVAL_PROPERTY,
    RISK_LEVEL_PROPERTY,
)
from semantic_kernel.functions.kernel_function_decorator import kernel_function


class BankPlugin:
    """A plugin with a destructive function, used to prove calls are (not) dispatched."""

    def __init__(self):
        self.transfers: list[int] = []

    @kernel_function(name="transfer", description="Transfer an amount of money.")
    def transfer(self, amount: int) -> str:
        self.transfers.append(amount)
        return f"transferred {amount}"

    @kernel_function(name="balance", description="Read the account balance.")
    def balance(self) -> str:
        return "balance is 100"


@fixture
def bank() -> BankPlugin:
    return BankPlugin()


@fixture
def kernel_with_bank(kernel: Kernel, bank: BankPlugin) -> Kernel:
    kernel.add_plugin(bank, plugin_name="bank")
    return kernel


def transfer_call(amount: int = 10, call_id: str = "call_1") -> FunctionCallContent:
    return FunctionCallContent(
        id=call_id, plugin_name="bank", function_name="transfer", arguments=f'{{"amount": {amount}}}'
    )


def balance_call(call_id: str = "call_2") -> FunctionCallContent:
    return FunctionCallContent(id=call_id, plugin_name="bank", function_name="balance", arguments="{}")


async def invoke(kernel: Kernel, call: FunctionCallContent, history: ChatHistory | None = None):
    history = history if history is not None else ChatHistory()
    context = await kernel.invoke_function_call(function_call=call, chat_history=history)
    return context, history


def add_auth_filter(kernel: Kernel, policy: FunctionAuthorizationPolicy) -> FunctionAuthorizationFilter:
    auth_filter = FunctionAuthorizationFilter(policy=policy)
    kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, auth_filter)
    return auth_filter


class TestFailClosedDefaults:
    async def test_unclassified_function_requires_approval(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """A function with no declared risk fails closed: suspended, never executed."""
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        _, history = await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        decision = auth_filter.audit_log[-1]
        assert decision.action == FunctionAuthorizationAction.REQUIRE_APPROVAL
        assert decision.status == FunctionAuthorizationStatus.PENDING_APPROVAL
        assert "pending_approval" in str(history.messages[-1].items[0].result)

    async def test_injection_cannot_bypass_the_checkpoint(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """Prompt injection can propose a call, but the filter still gates dispatch."""
        add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        malicious = transfer_call(amount=10000)
        await invoke(kernel_with_bank, malicious)

        assert bank.transfers == []

    async def test_invalid_declared_risk_fails_closed(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """A typo'd risk level in metadata is treated as the fail-closed default."""
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())
        function = kernel_with_bank.get_function("bank", "transfer")
        function.metadata.additional_properties = {RISK_LEVEL_PROPERTY: "no-such-level"}

        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].risk == FunctionRiskLevel.HIGH

    async def test_unmapped_risk_level_denies(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """A risk level missing from the action map fails closed to DENY."""
        policy = FunctionAuthorizationPolicy(
            risk_overrides={"bank-transfer": FunctionRiskLevel.HIGH},
            action_map={FunctionRiskLevel.LOW: FunctionAuthorizationAction.ALLOW},
        )
        auth_filter = add_auth_filter(kernel_with_bank, policy)

        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].action == FunctionAuthorizationAction.DENY


class TestPolicyClassification:
    async def test_low_risk_function_executes(self, kernel_with_bank: Kernel, bank: BankPlugin):
        policy = FunctionAuthorizationPolicy(risk_overrides={"bank-balance": FunctionRiskLevel.LOW})
        auth_filter = add_auth_filter(kernel_with_bank, policy)

        _, history = await invoke(kernel_with_bank, balance_call())

        decision = auth_filter.audit_log[-1]
        assert decision.status == FunctionAuthorizationStatus.EXECUTED
        assert "balance is 100" in str(history.messages[-1].items[0].result)

    async def test_plugin_wildcard_override(self, kernel_with_bank: Kernel, bank: BankPlugin):
        policy = FunctionAuthorizationPolicy(risk_overrides={"bank-*": FunctionRiskLevel.LOW})
        auth_filter = add_auth_filter(kernel_with_bank, policy)

        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == [10]
        assert auth_filter.audit_log[-1].status == FunctionAuthorizationStatus.EXECUTED

    async def test_exact_override_beats_wildcard(self, kernel_with_bank: Kernel, bank: BankPlugin):
        policy = FunctionAuthorizationPolicy(
            risk_overrides={"bank-*": FunctionRiskLevel.LOW, "bank-transfer": FunctionRiskLevel.CRITICAL}
        )
        auth_filter = add_auth_filter(kernel_with_bank, policy)

        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].action == FunctionAuthorizationAction.DENY

    async def test_declared_metadata_risk_is_honored(self, kernel_with_bank: Kernel, bank: BankPlugin):
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())
        function = kernel_with_bank.get_function("bank", "transfer")
        function.metadata.additional_properties = {RISK_LEVEL_PROPERTY: "low"}

        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == [10]
        assert auth_filter.audit_log[-1].risk == FunctionRiskLevel.LOW

    async def test_requires_approval_metadata_overrides_allow(self, kernel_with_bank: Kernel, bank: BankPlugin):
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())
        function = kernel_with_bank.get_function("bank", "transfer")
        function.metadata.additional_properties = {
            RISK_LEVEL_PROPERTY: "low",
            REQUIRES_APPROVAL_PROPERTY: True,
        }

        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].action == FunctionAuthorizationAction.REQUIRE_APPROVAL


class TestKeywordGuard:
    async def test_keyword_guard_escalates_low_risk(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """The deterministic guard escalates on suspicious argument content; strictest wins."""
        policy = FunctionAuthorizationPolicy(
            risk_overrides={"bank-*": FunctionRiskLevel.LOW},
            keyword_guard={"10000": FunctionRiskLevel.CRITICAL},
        )
        auth_filter = add_auth_filter(kernel_with_bank, policy)

        await invoke(kernel_with_bank, transfer_call(amount=10000))

        assert bank.transfers == []
        decision = auth_filter.audit_log[-1]
        assert decision.action == FunctionAuthorizationAction.DENY
        assert "keyword guard" in decision.reason

    async def test_keyword_guard_never_lowers_risk(self, kernel_with_bank: Kernel, bank: BankPlugin):
        policy = FunctionAuthorizationPolicy(
            risk_overrides={"bank-transfer": FunctionRiskLevel.CRITICAL},
            keyword_guard={"amount": FunctionRiskLevel.LOW},
        )
        auth_filter = add_auth_filter(kernel_with_bank, policy)

        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].risk == FunctionRiskLevel.CRITICAL


class TestApprovalBinding:
    async def test_grant_then_reissue_executes_once(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """Terminate-and-resume: grant the pending decision, re-issue the identical call."""
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        await invoke(kernel_with_bank, transfer_call())
        pending = auth_filter.audit_log[-1]
        assert pending.status == FunctionAuthorizationStatus.PENDING_APPROVAL

        auth_filter.grant_approval(pending)
        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == [10]
        approved = auth_filter.audit_log[-1]
        assert approved.status == FunctionAuthorizationStatus.EXECUTED
        assert approved.authority_source == "user_approval"

    async def test_changed_arguments_invalidate_approval(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """An approval for transfer(10) must not be replayable for transfer(10000)."""
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        await invoke(kernel_with_bank, transfer_call(amount=10))
        auth_filter.grant_approval(auth_filter.audit_log[-1])

        await invoke(kernel_with_bank, transfer_call(amount=10000))

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].status == FunctionAuthorizationStatus.PENDING_APPROVAL

    async def test_approval_is_single_use(self, kernel_with_bank: Kernel, bank: BankPlugin):
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        await invoke(kernel_with_bank, transfer_call())
        auth_filter.grant_approval(auth_filter.audit_log[-1])

        await invoke(kernel_with_bank, transfer_call())
        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == [10]
        assert auth_filter.audit_log[-1].status == FunctionAuthorizationStatus.PENDING_APPROVAL

    async def test_expired_approval_is_terminal_non_execution(self, kernel_with_bank: Kernel, bank: BankPlugin):
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        await invoke(kernel_with_bank, transfer_call())
        pending = auth_filter.audit_log[-1]
        auth_filter.grant_approval(pending)
        auth_filter.approvals._approvals[pending.binding] = time.time() - 1.0

        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].status == FunctionAuthorizationStatus.EXPIRED

    async def test_non_finite_or_non_positive_ttl_is_rejected(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """NaN/inf/zero TTLs would create approvals that never expire; they are rejected."""
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        await invoke(kernel_with_bank, transfer_call())
        pending = auth_filter.audit_log[-1]

        for bad_ttl in (float("nan"), float("inf"), 0.0, -1.0):
            with raises(ValueError):
                auth_filter.grant_approval(pending, ttl_seconds=bad_ttl)

        assert bank.transfers == []

    async def test_policy_change_invalidates_approval(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """An approval is bound to the policy snapshot that produced it."""
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        await invoke(kernel_with_bank, transfer_call())
        auth_filter.grant_approval(auth_filter.audit_log[-1])

        auth_filter.policy = FunctionAuthorizationPolicy(principal="someone_else")
        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []

    async def test_denied_cannot_be_converted_by_approval(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """A DENY decision is terminal: retrying with a granted approval stays denied."""
        policy = FunctionAuthorizationPolicy(risk_overrides={"bank-transfer": FunctionRiskLevel.CRITICAL})
        auth_filter = add_auth_filter(kernel_with_bank, policy)

        await invoke(kernel_with_bank, transfer_call())
        denied = auth_filter.audit_log[-1]
        assert denied.status == FunctionAuthorizationStatus.DENIED

        auth_filter.grant_approval(denied)
        await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].status == FunctionAuthorizationStatus.DENIED


class TestLoopAndModelSignals:
    async def test_pending_terminates_loop_by_default(self, kernel_with_bank: Kernel, bank: BankPlugin):
        add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        context, _ = await invoke(kernel_with_bank, transfer_call())

        assert context is not None
        assert context.terminate is True

    async def test_pending_without_terminate(self, kernel_with_bank: Kernel, bank: BankPlugin):
        add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy(terminate_on_pending=False))

        context, _ = await invoke(kernel_with_bank, transfer_call())

        assert context is None

    async def test_deny_feeds_refusal_to_model_without_terminating(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """The model gets a clean structured 'blocked' signal, not a silent no-op."""
        policy = FunctionAuthorizationPolicy(risk_overrides={"bank-transfer": FunctionRiskLevel.CRITICAL})
        add_auth_filter(kernel_with_bank, policy)

        context, history = await invoke(kernel_with_bank, transfer_call())

        assert context is None
        result = str(history.messages[-1].items[0].result)
        assert "denied" in result
        assert "not executed" in result


class TestAuditLog:
    async def test_audit_distinguishes_lifecycle_states(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """Proposed→pending, approved→executed, denied and expired are distinct records."""
        auth_filter = add_auth_filter(kernel_with_bank, FunctionAuthorizationPolicy())

        await invoke(kernel_with_bank, transfer_call())
        auth_filter.grant_approval(auth_filter.audit_log[-1])
        await invoke(kernel_with_bank, transfer_call())
        await invoke(kernel_with_bank, transfer_call())
        pending = auth_filter.audit_log[-1]
        auth_filter.grant_approval(pending)
        auth_filter.approvals._approvals[pending.binding] = time.time() - 1.0
        await invoke(kernel_with_bank, transfer_call())

        states = [decision.status for decision in auth_filter.audit_log]
        assert states == [
            FunctionAuthorizationStatus.PENDING_APPROVAL,
            FunctionAuthorizationStatus.EXECUTED,
            FunctionAuthorizationStatus.PENDING_APPROVAL,
            FunctionAuthorizationStatus.EXPIRED,
        ]
        assert len({decision.decision_id for decision in auth_filter.audit_log}) == 4

    def test_args_digest_is_order_independent(self):
        digest_a = FunctionAuthorizationFilter.canonical_args_digest({"a": 1, "b": 2})
        digest_b = FunctionAuthorizationFilter.canonical_args_digest({"b": 2, "a": 1})
        digest_c = FunctionAuthorizationFilter.canonical_args_digest({"a": 1, "b": 3})

        assert digest_a == digest_b
        assert digest_a != digest_c

    def test_decision_binding_covers_all_dimensions(self):
        base = dict(
            function_name="bank-transfer",
            args_digest="d1",
            principal="p1",
            policy_digest="s1",
            risk=FunctionRiskLevel.HIGH,
            action=FunctionAuthorizationAction.REQUIRE_APPROVAL,
            status=FunctionAuthorizationStatus.PENDING_APPROVAL,
            reason="r",
            authority_source="policy",
        )
        from semantic_kernel.filters import FunctionAuthorizationDecision

        reference = FunctionAuthorizationDecision(**base)
        for field, changed in [
            ("function_name", "bank-balance"),
            ("args_digest", "d2"),
            ("principal", "p2"),
            ("policy_digest", "s2"),
        ]:
            variant = FunctionAuthorizationDecision(**{**base, field: changed})
            assert variant.binding != reference.binding, field

    def test_digest_distinguishes_type_from_lookalike_str(self):
        """An object whose __str__ mimics an approved value must not collide."""

        class Lookalike:
            def __str__(self):
                return "approved"

        digest_str = FunctionAuthorizationFilter.canonical_args_digest({"x": "approved"})
        digest_obj = FunctionAuthorizationFilter.canonical_args_digest({"x": Lookalike()})

        assert digest_str != digest_obj

        # A native string crafted to mimic the object's tagged rendering must
        # not collide either: the structural type tag keeps the classes apart.
        rendered_obj = FunctionAuthorizationFilter.render_canonical_arguments({"x": Lookalike()})
        mimic = rendered_obj.split('["obj","', 1)[-1]
        digest_mimic = FunctionAuthorizationFilter.canonical_args_digest({"x": mimic})
        assert digest_mimic != digest_obj

    async def test_uncanonicalizable_arguments_fail_closed(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """Circular arguments deny and audit instead of crashing the gate open."""
        policy = FunctionAuthorizationPolicy(risk_overrides={"bank-*": FunctionRiskLevel.LOW})
        auth_filter = add_auth_filter(kernel_with_bank, policy)
        cyclic: dict = {}
        cyclic["self"] = cyclic

        async def poison_arguments(context, next):
            context.arguments["amount"] = cyclic
            await next(context)

        kernel_with_bank.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, poison_arguments)
        # poison_arguments was added last, so it runs innermost; re-add the
        # authorization filter so it is innermost again, after the poisoning.
        kernel_with_bank.remove_filter(filter_id=id(auth_filter))
        kernel_with_bank.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, auth_filter)

        _, history = await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        decision = auth_filter.audit_log[-1]
        assert decision.status == FunctionAuthorizationStatus.DENIED
        assert decision.args_digest == "uncanonicalizable"
        assert "denied" in str(history.messages[-1].items[0].result)

    async def test_dispatch_failure_is_recorded_as_failed(self, kernel_with_bank: Kernel, bank: BankPlugin):
        """If dispatch raises after authorization, the audit shows FAILED, not EXECUTED."""
        policy = FunctionAuthorizationPolicy(risk_overrides={"bank-*": FunctionRiskLevel.LOW})
        auth_filter = add_auth_filter(kernel_with_bank, policy)

        async def exploding_downstream(context, next):
            raise RuntimeError("downstream blew up")

        # Added last -> runs innermost, between the authorization filter and dispatch.
        kernel_with_bank.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, exploding_downstream)

        with raises(RuntimeError):
            await invoke(kernel_with_bank, transfer_call())

        assert bank.transfers == []
        assert auth_filter.audit_log[-1].status == FunctionAuthorizationStatus.FAILED

    async def test_warns_when_not_innermost_filter(self, kernel_with_bank: Kernel, bank: BankPlugin, caplog):
        """A filter registered between authorization and dispatch triggers a warning."""
        policy = FunctionAuthorizationPolicy(risk_overrides={"bank-*": FunctionRiskLevel.LOW})
        add_auth_filter(kernel_with_bank, policy)

        async def passthrough(context, next):
            await next(context)

        # Added last -> runs innermost, between the authorization filter and dispatch.
        kernel_with_bank.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, passthrough)

        with caplog.at_level("WARNING"):
            await invoke(kernel_with_bank, transfer_call())

        assert any("innermost" in record.message for record in caplog.records)

    def test_approval_store_expiry(self):
        from semantic_kernel.filters import FunctionApprovalStore

        store = FunctionApprovalStore()
        store.grant("binding", ttl_seconds=100)
        assert store.consume("binding") == "ok"
        assert store.consume("binding") == "absent"

        store.grant("binding", ttl_seconds=100)
        store._approvals["binding"] = time.time() - 1.0
        assert store.consume("binding") == "expired"
