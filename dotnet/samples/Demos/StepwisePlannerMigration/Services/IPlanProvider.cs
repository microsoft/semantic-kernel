// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary

using Microsoft.SemanticKernel.ChatCompletion;

#pragma warning restore IDE0005 // Using directive is unnecessary

namespace StepwisePlannerMigration.Services;

/// <summary>
/// Interface to get a previously generated plan from file for demonstration purposes.
/// </summary>
public interface IPlanProvider
{
    ChatHistory GetPlan(string fileName);
}
