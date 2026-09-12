// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Request body for Vertex AI <c>:embedContent</c> (Gemini Embedding 2 models).
/// </summary>
internal sealed class VertexAIEmbedContentRequest
{
    [JsonPropertyName("content")]
    public GeminiContent Content { get; set; } = null!;

    [JsonPropertyName("outputDimensionality")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? OutputDimensionality { get; set; }

    [JsonPropertyName("taskType")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? TaskType { get; set; }

    [JsonPropertyName("title")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Title { get; set; }

    public static VertexAIEmbedContentRequest FromText(string text, int? dimensions = null, EmbeddingGenerationOptions? options = null)
    {
        static string? GetTaskType(EmbeddingGenerationOptions? options)
        {
            if (options?.AdditionalProperties is not null)
            {
                object? taskType = null;

                if (options.AdditionalProperties.TryGetValue("task_type", out object? task_type) ||
                    options.AdditionalProperties.TryGetValue("tasktype", out taskType))
                {
                    return (task_type ?? taskType)?.ToString();
                }
            }

            return null;
        }

        static string? GetTitle(EmbeddingGenerationOptions? options)
        {
            if (options?.AdditionalProperties is not null)
            {
                if (options.AdditionalProperties.TryGetValue("title", out object? title))
                {
                    return title?.ToString();
                }
            }

            return null;
        }

        return new()
        {
            Content = new GeminiContent
            {
                Parts =
                [
                    new GeminiPart { Text = text }
                ]
            },
            OutputDimensionality = dimensions,
            TaskType = GetTaskType(options),
            Title = GetTitle(options),
        };
    }
}
