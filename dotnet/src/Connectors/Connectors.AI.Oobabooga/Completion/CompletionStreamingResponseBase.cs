// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion;

public class CompletionStreamingResponseBase
{
    public const string ResponseObjectTextStreamEvent = "text_stream";
    public const string ResponseObjectStreamEndEvent = "stream_end";

    /// <summary>
    /// A field used by Oobabooga to signal the type of websocket message sent, e.g. "text_stream" or "stream_end".
    /// </summary>
    [JsonPropertyName("event")]
    public string Event { get; set; } = string.Empty;

    /// <summary>
    /// A field used by Oobabooga to signal the number of messages sent, starting with 0 and incremented on each message.
    /// </summary>
    [JsonPropertyName("message_num")]
    public int MessageNum { get; set; }
}
