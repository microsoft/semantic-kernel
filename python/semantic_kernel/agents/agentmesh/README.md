# AgentMesh Integration for Semantic Kernel

AgentMesh trust and governance layer integration for Semantic Kernel - enabling cryptographic identity verification and policy-based governance for AI agents.

## Overview

This integration provides:

- **GovernedAgent**: Wrap agents with governance policies
- **GovernanceKernel**: Policy enforcement for kernel operations
- **Cryptographic Identity**: CMVK/Ed25519 based agent authentication
- **Trust Verification**: Multi-agent handshake protocols

## Usage

### Creating a Governed Agent

```python
from semantic_kernel.agents.agentmesh import (
    CMVKIdentity,
    GovernedAgent,
    GovernancePolicy,
)

# Generate cryptographic identity
identity = CMVKIdentity.generate(
    agent_name="assistant-agent",
    capabilities=["chat", "code_generation"]
)

# Define governance policy
policy = GovernancePolicy(
    max_requests_per_minute=30,
    allowed_functions=["chat", "generate_code"],
    audit_all_invocations=True,
    require_trust_verification=True,
)

# Create governed agent
governed_agent = GovernedAgent(
    agent=base_agent,
    identity=identity,
    policy=policy,
)
```

### Governance Kernel

```python
from semantic_kernel.agents.agentmesh import GovernanceKernel

# Wrap kernel with governance
governed_kernel = GovernanceKernel(
    kernel=kernel,
    identity=identity,
    policy=policy,
)

# Invoke with governance checks
result = await governed_kernel.invoke_function(
    "chat",
    invoker_card=requester_card,
    message="Hello",
)
```

### Trust Verification

```python
from semantic_kernel.agents.agentmesh import TrustHandshake, TrustedAgentCard

# Create agent card
card = TrustedAgentCard(
    name="my-agent",
    description="A helpful agent",
    capabilities=["chat"],
)
card.sign(identity)

# Verify peer before interaction
handshake = TrustHandshake(my_identity=identity)
result = handshake.verify_peer(peer_card)

if result.trusted:
    # Safe to interact
    pass
```

## Features

### GovernancePolicy

| Setting | Description | Default |
|---------|-------------|---------|
| `max_requests_per_minute` | Rate limit per minute | 60 |
| `max_requests_per_hour` | Rate limit per hour | 1000 |
| `allowed_functions` | Whitelist of functions | None (all) |
| `denied_functions` | Blacklist of functions | None |
| `max_concurrent_tasks` | Concurrent task limit | 10 |
| `audit_all_invocations` | Audit every call | False |
| `require_trust_verification` | Require identity | True |
| `min_trust_score` | Minimum trust score | 0.7 |

### Policy Violations

The governance layer tracks violations:

```python
violations = governed_kernel.get_violations()
for v in violations:
    print(f"{v.violation_type}: {v.details}")
```

### Audit Logging

```python
# Get audit log
audit_log = governed_kernel.get_audit_log()

# Get summary
summary = governed_kernel.get_governance_summary()
print(f"Total violations: {summary['total_violations']}")
```

## Security Model

Uses Ed25519 cryptography for:
- Agent identity generation
- Request signing
- Peer verification

## License

MIT License
