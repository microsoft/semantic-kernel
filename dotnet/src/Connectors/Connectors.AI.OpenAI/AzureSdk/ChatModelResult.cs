// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary> Represents a singular result of a chat completion.</summary>
public class ChatModelResult
{
    /// <summary> A unique identifier associated with this chat completion response. </summary>
    public string Id { get; }

    /// <summary>
    /// The first timestamp associated with generation activity for this completions response,
    /// represented as seconds since the beginning of the Unix epoch of 00:00 on 1 Jan 1970.
    /// </summary>
    public DateTimeOffset Created { get; }

    /// <summary>
    /// Content filtering results for zero or more prompts in the request.
    /// </summary>
    public IReadOnlyList<PromptFilterResult> PromptFilterResults { get; }

    /// <summary>
    /// The completion choice associated with this completion result.
    /// </summary>
    public ChatChoice Choice { get; }

    /// <summary> Usage information for tokens processed and generated as part of this completions operation. </summary>
    public CompletionsUsage Usage { get; }

    /// <summary> Initializes a new instance of TextModelResult. </summary>
    /// <param name="completionsData"> A completions respnse object to populate the fields relative the the response.</param>
    /// <param name="choiceData"> A choice object to populate the fields relative to the resulting choice.</param>
    internal ChatModelResult(ChatCompletions completionsData, ChatChoice choiceData)
    {
        this.Id = completionsData.Id;
        this.Created = completionsData.Created;
        this.PromptFilterResults = completionsData.PromptFilterResults;
        this.Choice = choiceData;
        this.Usage = completionsData.Usage;
    }
}
