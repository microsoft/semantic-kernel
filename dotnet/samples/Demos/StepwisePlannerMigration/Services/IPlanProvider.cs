// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;

namespace StepwisePlannerMigration.Services;

/// <summary>
/// Interface to get a previously generated plan from file for demonstration purposes.
/// </summary>
public interface IPlanProvider
{
    ChatHistory GetPlan(string fileName);
}
