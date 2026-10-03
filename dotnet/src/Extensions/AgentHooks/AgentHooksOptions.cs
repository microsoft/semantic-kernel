// Copyright (c) Microsoft. All rights reserved.

using System;
using AgentHooks;

namespace Microsoft.SemanticKernel.AgentHooks;

/// <summary>
/// Options for the AGENT-HOOKS-0.1 kernel adapter
/// (https://github.com/responsibleai/agent-hooks).
/// </summary>
public sealed class AgentHooksOptions
{
    /// <summary>Stable identifier for the agent definition (context <c>agent.id</c>).</summary>
    public string AgentId { get; set; } = "semantic-kernel-agent";

    /// <summary>
    /// Session identifier factory. Called once per <see cref="Kernel"/> instance;
    /// defaults to a random identifier per kernel.
    /// </summary>
    public Func<Kernel, string>? SessionIdProvider { get; set; }

    /// <summary>
    /// Composition profile and knobs in effect for every emission
    /// (AGENT-HOOKS-0.1 §7). Defaults to <c>sequential/first_deny</c> with
    /// <c>on_approval: stop</c>.
    /// </summary>
    public CompositionConfig Composition { get; set; } = CompositionConfig.Default;

    /// <summary>Enforcement mode (§8). Defaults to <see cref="EnforcementMode.Enforce"/>.</summary>
    public EnforcementMode Mode { get; set; } = EnforcementMode.Enforce;

    /// <summary>Optional approval resolver for liftable denies (§9).</summary>
    public IApprovalResolver? ApprovalResolver { get; set; }

    /// <summary>Optional per-emission record sink (§10.3), e.g. an audit pipeline.</summary>
    public Action<InterceptionRecord>? RecordSink { get; set; }

    /// <summary>
    /// Per-interceptor timeout (§7). <c>null</c> uses the SDK default of 5000 ms.
    /// </summary>
    public TimeSpan? InterceptorTimeout { get; set; }
}
