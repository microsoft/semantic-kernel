// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Object that contains details about a plan and its goal and details of its execution.
/// </summary>
public class SkillPlan
{
    /// <summary>
    /// Internal constant string representing the ID key.
    /// </summary>
    internal const string IdKey = "PLAN__ID";

    /// <summary>
    /// Internal constant string representing the goal key.
    /// </summary>
    internal const string GoalKey = "PLAN__GOAL";

    /// <summary>
    /// Internal constant string representing the plan key.
    /// </summary>
    internal const string PlanKey = "PLAN__PLAN";

    /// <summary>
    /// Internal constant string representing the is complete key.
    /// </summary>
    internal const string IsCompleteKey = "PLAN__ISCOMPLETE";

    /// <summary>
    /// Internal constant string representing the is successful key.
    /// </summary>
    internal const string IsSuccessfulKey = "PLAN__ISSUCCESSFUL";

    /// <summary>
    /// Internal constant string representing the result key.
    /// </summary>
    internal const string ResultKey = "PLAN__RESULT";

    /// <summary>
    /// The ID of the plan.
    /// Can be used to track creation of a plan and execution over multiple steps.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// The goal of the plan.
    /// </summary>
    [JsonPropertyName("goal")]
    public string Goal { get; set; } = string.Empty;

    /// <summary>
    /// The plan details in string.
    /// </summary>
    [JsonPropertyName("plan")]
    public string PlanString { get; set; } = string.Empty;

    /// <summary>
    /// The arguments for the plan.
    /// </summary>
    [JsonPropertyName("arguments")]
    public string Arguments { get; set; } = string.Empty;

    /// <summary>
    /// Flag indicating if the plan is complete.
    /// </summary>
    [JsonPropertyName("is_complete")]
    public bool IsComplete { get; set; }

    /// <summary>
    /// Flag indicating if the plan is successful.
    /// </summary>
    [JsonPropertyName("is_successful")]
    public bool IsSuccessful { get; set; }

    /// <summary>
    /// The result of the plan execution.
    /// </summary>
    [JsonPropertyName("result")]
    public string Result { get; set; } = string.Empty;

    /// <summary>
    /// To help with writing plans to <see cref="Orchestration.ContextVariables"/>.
    /// </summary>
    /// <returns>JSON string representation of the Plan</returns>
    public string ToJson()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// To help with reading plans from <see cref="Orchestration.ContextVariables"/>.
    /// </summary>
    /// <param name="json">JSON string representation of aPlan</param>
    /// <returns>An instance of a Plan object.</returns>
    public static SkillPlan FromJson(string json)
    {
        return JsonSerializer.Deserialize<SkillPlan>(json) ?? new SkillPlan();
    }
}
