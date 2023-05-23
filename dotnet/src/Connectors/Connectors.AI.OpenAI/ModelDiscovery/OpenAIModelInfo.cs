// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ModelDiscovery;

internal sealed class OpenAIModelInfo
{
    private static string[] ChatCompletionModels = { "gpt-4", "gpt-4-0314", "gpt-4-32k", "gpt-4-32k-0314", "gpt-3.5-turbo", "gpt-3.5-turbo-0301" };
    private static string[] TextCompetionModels = { "text-davinci-003", "text-davinci-002", "text-curie-001", "text-babbage-001", "text-ada-001" };
    private static string[] TextEmbeddingModels = { "text-embedding-ada-002", "text-search-ada-doc-001" };

    [JsonConstructor]
    public OpenAIModelInfo(string id)
    {
        this.Id = id;
        this.Capabilities = ModelCapabilities.InitializeWithKnownModels(id);
    }

    /// <summary>
    /// The identity of this item.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// The capabilities of a base or fine tune model.
    /// </summary>
    [JsonIgnore]
    public ModelCapabilities Capabilities { get; }

    internal sealed class ModelCapabilities
    {
        public static ModelCapabilities InitializeWithKnownModels(string model)
        {
            return new ModelCapabilities()
            {
                SupportsChatCompletion = ChatCompletionModels.Contains(model, StringComparer.OrdinalIgnoreCase),
                SupportsTextCompletion = TextCompetionModels.Contains(model, StringComparer.OrdinalIgnoreCase),
                SupportsEmbeddings = TextEmbeddingModels.Contains(model, StringComparer.OrdinalIgnoreCase),
            };
        }

        /// <summary>
        /// A value indicating whether a model supports completion.
        /// </summary>
        [JsonPropertyName("chat")]
        public bool SupportsChatCompletion { get; set; }

        /// <summary>
        /// A value indicating whether a model supports completion.
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
