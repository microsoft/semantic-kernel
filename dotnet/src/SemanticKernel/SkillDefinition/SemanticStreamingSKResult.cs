// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using System.Threading.Tasks;
using System.Threading;

namespace Microsoft.SemanticKernel.SkillDefinition;
internal record SemanticStreamingSKResult : StreamingSKResult
{
    private readonly Func<CancellationToken, IAsyncEnumerable<ITextStreamingResult>> _streamingResultDelegate;
    private readonly Func<CancellationToken, Task<Stream>> _rawStreamResultDelegate;

    public SemanticStreamingSKResult(SKContext inputContext, Func<CancellationToken, IAsyncEnumerable<ITextStreamingResult>> streamingResultDelegate, Func<CancellationToken, Task<Stream>> rawStreamResultDelegate)
        : base(inputContext)
    {
        this._streamingResultDelegate = streamingResultDelegate;
        this._rawStreamResultDelegate = rawStreamResultDelegate;
    }

    public override Task<Stream> GetRawStream(CancellationToken cancellationToken = default)
        => this._rawStreamResultDelegate(cancellationToken);

    public override IAsyncEnumerable<ITextStreamingResult> GetResults(CancellationToken cancellationToken = default)
        => this._streamingResultDelegate(cancellationToken);

    public override async Task<SKContext> GetOutputSKContextAsync(CancellationToken cancellationToken = default)
    {
        var outputContext = this.InputSKContext.Clone();
        ITextStreamingResult? firstResult = null;
        var modelResults = new List<ModelResult>();

        await foreach (ITextStreamingResult completionResult in this._streamingResultDelegate(cancellationToken))
        {
            firstResult ??= completionResult;
            modelResults.Add(completionResult.ModelResult);
        }

        outputContext.ModelResults = modelResults;
        outputContext.Variables.Update(await firstResult!.GetCompletionAsync(cancellationToken).ConfigureAwait(false));

        // To avoid any unexpected behavior we only take the first completion result (when running from the Kernel)
        return outputContext;
    }
}
