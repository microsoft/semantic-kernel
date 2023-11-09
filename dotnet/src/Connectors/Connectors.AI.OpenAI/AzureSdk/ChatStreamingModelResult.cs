// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary> Represents a singular result of a chat completion.</summary>
public class ChatStreamingModelResult
{
    /// <summary> A unique identifier associated with this chat completion response. </summary>
    public string Id { get; }

    /// <summary>
    /// The first timestamp associated with generation activity for this completions response,
    /// represented as seconds since the beginning of the Unix epoch of 00:00 on 1 Jan 1970.
    /// </summary>
    public DateTimeOffset Created { get; }

    /// <summary>
    /// The reason the chat stream ended.
    /// </summary>
    public CompletionsFinishReason FinishReason { get; }

    /// <summary> Initializes a new instance of <see cref="ChatStreamingModelResult"/>. </summary>
    internal ChatStreamingModelResult(CompletionsFinishReason finishReason, string id, DateTimeOffset created)
    {
        this.Id = id;
        this.Created = created;
        this.FinishReason = finishReason;
    }
}
