// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.AI.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

public sealed class TextModelResult
{
    public string Id { get; }

    public DateTimeOffset Created { get; }

    public IReadOnlyList<PromptFilterResult> PromptFilterResults { get; }

    public Choice Choice { get; }

    /// <summary> Usage information for tokens processed and generated as part of this completions operation. </summary>
    public CompletionsUsage Usage { get; }

    internal TextModelResult(Completions resultData, Choice choice)
    {
        this.Id = resultData.Id;
        this.Created = resultData.Created;
        this.PromptFilterResults = resultData.PromptFilterResults;
        this.Choice = choice;
        this.Usage = resultData.Usage;
    }
}
