// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text.Json;

#pragma warning disable IDE0005 // Using directive is unnecessary

using Microsoft.SemanticKernel.ChatCompletion;

#pragma warning restore IDE0005 // Using directive is unnecessary

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
