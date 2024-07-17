// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;

namespace StepwisePlannerMigration.Services;

/// <summary>
/// Class to get a previously generated plan from file for demonstration purposes.
/// </summary>
public class PlanProvider : IPlanProvider
{
    public ChatHistory GetPlan(string fileName)
    {
        var plan = File.ReadAllText($"Resources/{fileName}");
        return JsonSerializer.Deserialize<ChatHistory>(plan)!;
    }
}
