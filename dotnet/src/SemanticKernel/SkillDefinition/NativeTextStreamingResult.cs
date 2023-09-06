// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

internal class NativeTextStreamingResult : ITextStreamingResult
{
    private readonly string _textResult;

    public ModelResult ModelResult => new(this._textResult);

    public NativeTextStreamingResult(string textResult)
    {
        this._textResult = textResult;
    }
    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._textResult);
    }

    public IAsyncEnumerable<string> GetCompletionStreamingAsync(CancellationToken cancellationToken = default)
    {
        return new[] { this._textResult }.ToAsyncEnumerable();
    }
}
