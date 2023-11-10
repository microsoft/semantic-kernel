// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Models;

public class ThreadRunStepListModel
{
    [JsonPropertyName("object")]
    public string Object { get; set; }

    [JsonPropertyName("data")]
    public List<ThreadRunStepModel> Data { get; set; }

    [JsonPropertyName("first_id")]
    public string FirstId { get; set; }

    [JsonPropertyName("last_id")]
    public string LastId { get; set; }

    [JsonPropertyName("has_more")]
    public bool HasMore { get; set; }
}
