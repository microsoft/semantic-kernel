// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary> Represents a singular result of a chat completion.</summary>
public class StreamingChatModelResult
{
    /// <summary> A unique identifier associated with this chat completion response. </summary>
    public string Id { get; }

    /// <summary>
    /// The first timestamp associated with generation activity for this completions response,
    /// represented as seconds since the beginning of the Unix epoch of 00:00 on 1 Jan 1970.
    /// </summary>
    public DateTimeOffset Created { get; }

    /// <summary>
    /// The completion choice associated with this completion result.
    /// </summary>
    public StreamingChatChoice Choice { get; }

    /// <summary> Initializes a new instance of ChatModelResult. </summary>
    /// <param name="completionsData"> A completions response object to populate the fields relative the response.</param>
    /// <param name="choiceData"> A choice object to populate the fields relative to the resulting choice.</param>
    internal StreamingChatModelResult(StreamingChatCompletions completionsData, StreamingChatChoice choiceData)
    {
        this.Id = completionsData.Id;
        this.Created = completionsData.Created;
        this.Choice = choiceData;
    }
}
