// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary> Represents a singular result of a completion.</summary>
public abstract class OpenAiModelResult
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

    /// <summary> Usage information for tokens processed and generated as part of this completions operation. </summary>
    public CompletionsUsage Usage { get; }

    protected OpenAiModelResult(string id, DateTimeOffset created, IReadOnlyList<PromptFilterResult> promptFilterResults, CompletionsUsage usage)
    {
        this.Id = id;
        this.Created = created;
        this.PromptFilterResults = promptFilterResults;
        this.Usage = usage;
    }
}
