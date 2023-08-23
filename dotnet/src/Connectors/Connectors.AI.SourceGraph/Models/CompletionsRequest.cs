// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using System.Text.Json.Serialization;

#pragma warning disable CS8618, CS8601, CS8603
internal class CompletionsRequest
{
    [JsonPropertyName("messages")]
    public Message[] Messages { get; set; } = Array.Empty<Message>();

    [JsonPropertyName("maxTokensToSample")]
    public int MaxTokens { get; set; } = 0;

    [JsonPropertyName("temperature")]
    public float Temperature { get; set; } = 0.0f;

    [JsonPropertyName("topP")]
    public int TopP { get; set; } = 1;

    [JsonPropertyName("frequnecyPenalty")]
    public int FrequencyPenalty { get; set; } = 0;

    [JsonPropertyName("presencePenalty")]
    public int PresencePenalty { get; set; } = 0;

    [JsonPropertyName("stopSequences")]
    public string[]? StopSequences { get; set; }


    private List<object> GetMessages()
    {
        List<object> messages = new();

        foreach (var message in Messages)
        {
            messages.Add(new
            {
                speaker = message.Speaker.ToString().ToLower(),
                text = message.Text
            });
        }

        return messages;
    }


    public HttpRequestMessage Build()
    {
        var path = "/.api/completions/stream";
        Dictionary<string, object> payload = new()
        {
            { "messages", GetMessages() },
            { "maxTokensToSample", MaxTokens },
            { "temperature", Temperature },
            { "topP", TopP },
            { "frequencyPenalty", FrequencyPenalty },
            { "presencePenalty", PresencePenalty },
            { "stopSequences", StopSequences ?? Array.Empty<string>() },
            { "streaming", true }
        };

        var request = HttpRequest.CreatePostRequest(path, payload);
        Console.WriteLine(request.RequestUri);
        return request;
    }


    public Dictionary<string, object> GetPayload() => new()
    {
        { "messages", GetMessages() },
        { "maxTokensToSample", MaxTokens },
        { "temperature", Temperature },
        { "topP", TopP },
        { "frequencyPenalty", FrequencyPenalty },
        { "presencePenalty", PresencePenalty },
        { "stopSequences", StopSequences ?? Array.Empty<string>() },
        { "streaming", true }
    };

}
