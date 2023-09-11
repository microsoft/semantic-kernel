// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using System.Threading.Tasks;
using System.Threading;

namespace Microsoft.SemanticKernel.SkillDefinition;
internal record SemanticStreamingSKResult : StreamingSKResult
{
    private readonly Func<CancellationToken, IEnumerable<ITextStreamingResult>> _getChoicesDelegate;

    public SemanticStreamingSKResult(SKContext inputContext,
        Func<CancellationToken, IEnumerable<ITextStreamingResult>> getChoicesDelegate)
        : base(inputContext)
    {
        this._getChoicesDelegate = getChoicesDelegate;
    }

    public override IEnumerable<IStreamingChoice> GetChoices(CancellationToken cancellationToken = default)
        => this._getChoicesDelegate(cancellationToken);

    public override async Task<IEnumerable<SKContext>> GetChoiceContextsAsync(CancellationToken cancellationToken = default)
    {
        var skContexts = new List<SKContext>();

        foreach (IStreamingChoice choice in this._getChoicesDelegate(cancellationToken))
        {
            var modelResults = new List<ModelResult>();
            var outputContext = this.InputContext.Clone();
            if (choice is ITextStreamingResult textChoice)
            {
                modelResults.Add(textChoice.ModelResult);
                outputContext.ModelResults = modelResults;
                outputContext.Variables.Update(await textChoice.GetCompletionAsync(cancellationToken).ConfigureAwait(false));
            }
            else
            {
                outputContext.Variables.Update(
                    StreamingSKResult.GetStringFromStream(
                        await choice.GetRawStreamAsync(cancellationToken).ConfigureAwait(false)));
            }

            skContexts.Add(outputContext);
        }

        return skContexts;
    }
}
