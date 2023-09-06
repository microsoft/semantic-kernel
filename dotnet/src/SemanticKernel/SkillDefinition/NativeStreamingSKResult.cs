// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

internal record NativeStreamingSKResult : StreamingSKResult
{
    private readonly Stream _rawStream;
    private readonly SKContext _outputContext;
    private Func<CancellationToken, IAsyncEnumerable<ITextStreamingResult>> _getResults;

    public NativeStreamingSKResult(SKContext inputContext, string content, SKContext outputContext)
        : this(inputContext, StreamingSKResult.GetStreamFromString(content), outputContext)
    {
    }

    public NativeStreamingSKResult(SKContext inputContext, Stream rawStream, SKContext outputContext, Func<CancellationToken, IAsyncEnumerable<ITextStreamingResult>>? getResults = null)
        : base(inputContext)
    {
        this._rawStream = rawStream;
        this._outputContext = outputContext;
        this._getResults = getResults ?? this.DefaultGetResults;
    }

    public override Task<SKContext> GetOutputSKContextAsync(CancellationToken cancellationToken = default) =>
        Task.FromResult(this._outputContext);

    public override Task<Stream> GetRawStream(CancellationToken cancellationToken = default) =>
        Task.FromResult(this._rawStream);

    public override IAsyncEnumerable<ITextStreamingResult> GetResults(CancellationToken cancellationToken = default) =>
        this._getResults(cancellationToken);

    private async IAsyncEnumerable<ITextStreamingResult> DefaultGetResults([EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var streamReader = new StreamReader(this._rawStream);
        var content = await streamReader.ReadToEndAsync().ConfigureAwait(false);
        yield return new NativeTextStreamingResult(content);
    }
}
