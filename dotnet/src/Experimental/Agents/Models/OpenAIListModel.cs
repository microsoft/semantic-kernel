// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

/// <summary>
/// list of run steps belonging to a run.
/// </summary>
internal abstract class OpenAIListModel<TModel>
{
    /// <summary>
    /// List of steps.
    /// </summary>
    [JsonPropertyName("data")]
    public List<TModel> Data { get; set; } = new List<TModel>();

    /// <summary>
    /// The identifier of the first data record.
    /// </summary>
    [JsonPropertyName("first_id")]
    public string FirstId { get; set; } = string.Empty;

    /// <summary>
    /// The identifier of the last data record.
    /// </summary>
    [JsonPropertyName("last_id")]
    public string LastId { get; set; } = string.Empty;

    /// <summary>
    /// Indicates of more pages of data exist.
    /// </summary>
    [JsonPropertyName("has_more")]
    public bool HasMore { get; set; }
}
