// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Connectors.Amazon.Models.Mistral;

/// <summary>
/// Mistral Text Response body.
/// </summary>
[Serializable]
public class MistralTextResponse
{
    /// <summary>
    /// A list of outputs from the model.
    /// </summary>
    [JsonPropertyName("outputs")]
    public List<Output>? Outputs { get; set; }

    /// <summary>
    /// Output parameters for the list of outputs of the text response.
    /// </summary>
    public class Output
    {
        /// <summary>
        /// The text that the model generated.
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }

        /// <summary>
        /// The reason why the response stopped generating text.
        /// </summary>
        [JsonPropertyName("stop_reason")]
        public string? StopReason { get; set; }
    }
}
