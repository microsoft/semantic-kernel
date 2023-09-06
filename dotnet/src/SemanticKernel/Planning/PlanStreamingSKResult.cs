// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning;

internal record PlanStreamingSKResult : StreamingSKResult
{
    private readonly string _content;
    private readonly SKContext _outputContext;

    public PlanStreamingSKResult(SKContext inputContext, string content, SKContext outputContext)
        : base(inputContext)
    {
        this._content = content;
        this._outputContext = outputContext;
    }

    public override Task<SKContext> GetOutputSKContextAsync(CancellationToken cancellationToken = default) =>
        Task.FromResult(this._outputContext);

    public override Task<Stream> GetRawStream(CancellationToken cancellationToken = default)
        => Task.FromResult(StreamingSKResult.GetStreamFromString(this._content));

    public override IAsyncEnumerable<ITextStreamingResult> GetResults(CancellationToken cancellationToken = default) =>
        new[] { new NativeTextStreamingResult(this._content) }.ToAsyncEnumerable();
}
