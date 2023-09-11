// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

internal record NativeStreamingSKResult : StreamingSKResult
{
    private readonly Stream _rawStream;
    private readonly SKContext _outputContext;
    private Func<CancellationToken, IEnumerable<IStreamingChoice>> _getChoices;

    public NativeStreamingSKResult(SKContext inputContext, string content, SKContext outputContext)
        : this(inputContext, StreamingSKResult.GetStreamFromString(content), outputContext)
    {
    }

    public NativeStreamingSKResult(SKContext inputContext, Stream rawStream, SKContext outputContext, Func<CancellationToken, IEnumerable<IStreamingChoice>>? getChoices = null)
        : base(inputContext)
    {
        this._rawStream = rawStream;
        this._outputContext = outputContext;
        this._getChoices = getChoices ?? this.DefaultGetChoices;
    }

    private IEnumerable<IStreamingChoice> DefaultGetChoices(CancellationToken cancellationToken)
    {
        yield return new NativeStreamingChoice(this._rawStream);
    }

    public override Task<IEnumerable<SKContext>> GetChoiceContextsAsync(CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public override IEnumerable<IStreamingChoice> GetChoices(CancellationToken cancellationToken = default)
        => this._getChoices(cancellationToken);
}
