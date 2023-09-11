// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
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

    public override Task<IEnumerable<SKContext>> GetChoiceContextsAsync(CancellationToken cancellationToken = default) =>
        Task.FromResult<IEnumerable<SKContext>>(new[] { this._outputContext });

    public override IEnumerable<IStreamingChoice> GetChoices(CancellationToken cancellationToken = default) =>
        new[] { new NativeStreamingChoice(this._content) };
}
