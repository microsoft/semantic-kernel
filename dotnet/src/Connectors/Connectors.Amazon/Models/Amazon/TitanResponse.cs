// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models.Amazon;

public class TitanResponse
{
    [JsonPropertyName("inputTextTokenCount")]
    public int InputTextTokenCount { get; set; }

    [JsonPropertyName("results")]
    public required IReadOnlyList<AmazonTitanTextCompletionResult> Results { get; set; }

    public IReadOnlyList<ChatMessageContent> GetResults()
    {
        return Results;
    }
}

public class AmazonTitanTextCompletionResult : ChatMessageContent
{
    [JsonPropertyName("tokenCount")]
    public int TokenCount { get; set; }

    [JsonPropertyName("outputText")]
    public required string OutputText { get; set; }

    [JsonPropertyName("completionReason")]
    public string? CompletionReason { get; set; }

    ModelResult ITextResult.ModelResult => new(OutputText);

    Task<string> ITextResult.GetCompletionAsync(CancellationToken cancellationToken)
    {
        return Task.FromResult(OutputText);
    }
}
