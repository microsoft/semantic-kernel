// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// Factory for creating a planner.
/// </summary>
/// <param name="chatKernel">The current semantic kernel used for the chat.</param>
/// <returns>The planner</returns>
public delegate Task<SequentialPlanner> PlannerFactoryAsync(IKernel chatKernel);
