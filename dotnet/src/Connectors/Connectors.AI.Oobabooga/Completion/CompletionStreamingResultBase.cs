// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion;

public abstract class CompletionStreamingResultBase
{
    internal readonly List<CompletionStreamingResponseBase> ModelResponses = new();
    public ModelResult ModelResult { get; }

    protected CompletionStreamingResultBase()
    {
        this.ModelResult = new ModelResult(this.ModelResponses);
    }

    public abstract void AppendResponse(CompletionStreamingResponseBase response);
    public abstract void SignalStreamEnd();
}
