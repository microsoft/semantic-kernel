// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// OpenAI settings.
/// </summary>
public class OpenAIConfig
{
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum TextGenerationTypes
    {
        Auto = 0,
        TextCompletion,
        Chat,
    }

    /// <summary>
    /// Model used for text generation. Chat models can be used too.
    /// </summary>
    public string TextModel { get; set; } = string.Empty;

    /// <summary>
    /// The type of OpenAI completion to use, either Text (legacy) or Chat.
    /// When using Auto, the client uses OpenAI model names to detect the correct protocol.
    /// Most OpenAI models use Chat. If you're using a non-OpenAI model, you might want to set this manually.
    /// </summary>
    public TextGenerationTypes TextGenerationType { get; set; } = TextGenerationTypes.Auto;

    /// <summary>
    /// Model used to embedding generation.
    /// </summary>
    public string EmbeddingModel { get; set; } = string.Empty;

    /// <summary>
    /// OpenAI HTTP endpoint. You may need to override this to work with
    /// OpenAI compatible services like LM Studio.
    /// </summary>
    public string Endpoint { get; set; } = "https://api.openai.com/v1";

    /// <summary>
    /// OpenAI API key.
    /// </summary>
    public string APIKey { get; set; } = string.Empty;

    /// <summary>
    /// Optional OpenAI Organization ID.
    /// </summary>
    public string? OrgId { get; set; } = string.Empty;

    /// <summary>
    /// The number of dimensions output embeddings should have.
    /// Only supported in "text-embedding-3" and later models developed with
    /// MRL, see https://arxiv.org/abs/2205.13147
    /// </summary>
    public int? EmbeddingDimensions { get; set; }

    /// <summary>
    /// Verify that the current state is valid.
    /// </summary>
    public void Validate()
    {
        if (string.IsNullOrWhiteSpace(this.APIKey))
        {
            throw new ConfigurationException($"OpenAI: {nameof(this.APIKey)} is empty");
        }

        if (this.EmbeddingDimensions is < 1)
        {
            throw new ConfigurationException($"OpenAI: {nameof(this.EmbeddingDimensions)} cannot be less than 1");
        }
    }
}
