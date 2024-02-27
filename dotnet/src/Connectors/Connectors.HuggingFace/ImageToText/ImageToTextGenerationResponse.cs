// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using static Microsoft.SemanticKernel.Connectors.HuggingFace.Core.TextGenerationResponse;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.ImageToText;

internal sealed class ImageToTextGenerationResponse : List<GeneratedTextItem>
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
