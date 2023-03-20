// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Backends.HuggingFace.HttpSchema;

public sealed class CompletionResponse
{
    public sealed class Choice
    {
        [JsonPropertyName("text")]
        public string? Text { get; set; }
    }

    [JsonPropertyName("choices")]
    public IList<Choice>? Choices { get; set; }
}
