// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Models;

/// <summary>
/// list of run steps belonging to a run.
/// </summary>
public class ThreadRunStepListModel
{
    /// <summary>
    /// Always "list"
    /// </summary>
    [JsonPropertyName("object")]
#pragma warning disable CA1720 // Identifier contains type name - We don't control the schema
    public string Object { get; set; } = "list";
#pragma warning restore CA1720 // Identifier contains type name

    /// <summary>
    /// LIst of steps.
    /// </summary>
    [JsonPropertyName("data")]
    public List<ThreadRunStepModel> Data { get; set; } = new List<ThreadRunStepModel>();

    [JsonPropertyName("first_id")]
    public string FirstId { get; set; } = string.Empty;

    [JsonPropertyName("last_id")]
    public string LastId { get; set; } = string.Empty;

    [JsonPropertyName("has_more")]
    public bool HasMore { get; set; }
}
