// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using static Microsoft.SemanticKernel.Connectors.HuggingFace.Core.TextGenerationResponse;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

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
