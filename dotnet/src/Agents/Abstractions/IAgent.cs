// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents;
/// <summary>
/// Interface for all Semantic Kernel agents. An agent instance
/// may participate in one or more conversations, or <see cref="AgentChat"/>.
/// A conversation may include one or more agents.
/// </summary>
/// <remarks>
/// In addition to identity and descriptive meta-data, an <see cref="IAgent"/>
/// must define its communication protocol, or <see cref="AgentChannel"/>.
/// </remarks>
public interface IAgent
{
    /// <summary>
    /// The description of the agent (optional)
    /// </summary>
    string? Description { get; init; }

    /// <summary>
    /// The identifier of the agent (optional).
    /// </summary>
    /// <remarks>
    /// Default to a random guid value, but may be overridden.
    /// </remarks>
    string Id { get; init; }

    /// <summary>
    /// A <see cref="ILoggerFactory"/> for this <see cref="IAgent"/>.
    /// </summary>
    ILoggerFactory LoggerFactory { get; init; }

    /// <summary>
    /// The name of the agent (optional)
    /// </summary>
    string? Name { get; init; }
}
