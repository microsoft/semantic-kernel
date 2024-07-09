// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;

namespace Connectors.Amazon.Models.Amazon;

public class TitanChatResponse
{
    [JsonPropertyName("inputTextTokenCount")]
    public int InputTextTokenCount { get; set; }

    [JsonPropertyName("results")]
    public required IReadOnlyList<AmazonTitanChatCompletionResult> Results { get; set; }

    public IReadOnlyList<ChatMessageContent> GetResults()
    {
        return Results;
    }
}

public class AmazonTitanChatCompletionResult : ChatMessageContent
{
    [JsonPropertyName("tokenCount")]
    public int TokenCount { get; set; }

    [JsonPropertyName("outputText")]
    public required string OutputText { get; set; }

    [JsonPropertyName("completionReason")]
    public string? CompletionReason { get; set; }

    // ModelResult ITextResult.ModelResult => new(OutputText);
    //
    // Task<string> ITextResult.GetCompletionAsync(CancellationToken cancellationToken)
    // {
    //     return Task.FromResult(OutputText);
    // }
}

[Serializable]
public class TitanTextResponse
{
    [JsonPropertyName("inputTextTokenCount")]
    public int InputTextTokenCount { get; set; }

    [JsonPropertyName("results")]
    public List<Result> Results { get; set; }

    public class Result
    {
        [JsonPropertyName("tokenCount")]
        public int TokenCount { get; set; }

        [JsonPropertyName("outputText")]
        public string OutputText { get; set; }

        [JsonPropertyName("completionReason")]
        public string CompletionReason { get; set; }
    }

    public class TitanStreamResponse
    {
        [JsonPropertyName("chunk")]
        public Chunk Chunks { get; set; }

        public class Chunk
        {
            [JsonPropertyName("bytes")]
            public string BytesBase64 { get; set; }

            public byte[] Bytes
            {
                get
                {
                    return Convert.FromBase64String(BytesBase64);
                }
            }
        }

        public class DecodedResponse
        {
            [JsonPropertyName("index")]
            public int Index { get; set; }

            [JsonPropertyName("inputTextTokenCount")]
            public int InputTextTokenCount { get; set; }

            [JsonPropertyName("totalOutputTextTokenCount")]
            public int TotalOutputTextTokenCount { get; set; }

            [JsonPropertyName("outputText")]
            public string OutputText { get; set; }

            [JsonPropertyName("completionReason")]
            public string CompletionReason { get; set; }
        }

        public DecodedResponse GetDecodedResponse()
        {
            string jsonString = Encoding.UTF8.GetString(Chunks.Bytes);
            return JsonSerializer.Deserialize<DecodedResponse>(jsonString);
        }
    }
}
