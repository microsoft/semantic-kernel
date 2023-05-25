// Copyright (c) Microsoft. All rights reserved.

using Newtonsoft.Json;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for the planner.
/// </summary>
public class PlannerOptions
{
    public const string PropertyName = "Planner";

    /// <summary>
    /// Define if the planner must be Sequential or not.
    /// </summary>
    [JsonProperty("Type")]
    public string PlannerType { get; set; } = string.Empty;
}
