// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// Defines the handoff relationships for a given agent.
/// </summary>
public sealed class HandoffConnections : Dictionary<string, string>;

/// <summary>
/// Handoff relationships post-processed into a name based lookup table that includes the agent type.
/// </summary>
internal sealed class HandoffLookup : Dictionary<string, (AgentType agentType, string description)>;
