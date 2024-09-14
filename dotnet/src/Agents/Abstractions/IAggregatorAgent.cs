// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Interface for aggregator agents that manage multiple agents and their interactions.
/// </summary>
public interface IAggregatorAgent
{
    /// <summary>
    /// The mode of the aggregator, defining how it aggregates the interactions.
    /// </summary>
    AggregatorMode Mode { get; init; }
}
