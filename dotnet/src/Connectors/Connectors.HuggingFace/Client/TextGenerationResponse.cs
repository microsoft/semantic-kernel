// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using static Microsoft.SemanticKernel.Connectors.HuggingFace.Client.TextGenerationResponse;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

internal sealed class TextGenerationResponse : List<GeneratedTextItem>
{
    internal sealed class GeneratedTextItem
    {
        /// <summary>
        /// The continuated string
        /// </summary>
        [JsonPropertyName("generated_text")]
        public string? GeneratedText { get; set; }
    }
}
