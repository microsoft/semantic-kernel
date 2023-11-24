// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Planner config with semantic memory
/// </summary>
public class PlannerConfig : PlannerConfigBase
{
    /// <summary>
    /// Semantic Memory configuration, used to enable function filtering during plan creation.
    /// </summary>
    /// <remarks>
    /// This configuration will be ignored if GetAvailableFunctionsAsync is set.
    /// </remarks>
    public SemanticMemoryConfig SemanticMemoryConfig { get; set; } = new();
}
