// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ModelDiscovery;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
[System.Diagnostics.CodeAnalysis.SuppressMessage("Build",
    "CA1812:'AzureModelInfo' is an internal class that is apparently never instantiated.", Justification = "JSON object")]
internal sealed class AzureModelInfo
{
    /// <summary>
    /// The identity of this item.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// The base model ID if this is a fine tune model; otherwise null.
    /// </summary>
    [JsonPropertyName("model")]
    public string? FineTuneBaseModel { get; set; }

    /// <summary>
    /// The fine tune job ID if this is a fine tune model; otherwise null.
    /// </summary>
    [JsonPropertyName("fine_tune")]
    public string? FineTune { get; set; }

    /// <summary>
    /// The capabilities of a base or fine tune model.
    /// </summary>
    [JsonPropertyName("capabilities")]
    public ModelCapabilities Capabilities { get; set; }

    /// <summary>
    /// A timestamp when this job or item was created (in unix epochs).
    /// </summary>
    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    /// <summary>
    /// A timestamp when this job or item was modified last (in unix epochs).
    /// </summary>
    [JsonPropertyName("updated_at")]
    public long UpdatedAt { get; set; }

    internal sealed class ModelCapabilities
    {
        /// <summary>
        /// A value indicating whether a model supports chat completion.
        /// </summary>
        /// <remarks>Not supported by Azure OpenAPI API</remarks>
        [JsonPropertyName("completion")]
        public bool SupportsChatCompletion { get; set; }

        /// <summary>
        /// A value indicating whether a model supports text completion.
        /// </summary>
        [JsonPropertyName("completion")]
        public bool SupportsTextCompletion { get; set; }

        /// <summary>
        /// A value indicating whether a model supports embeddings.
        /// </summary>
        [JsonPropertyName("embeddings")]
        public bool SupportsEmbeddings { get; set; }
    }
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider declaring as nullable.
