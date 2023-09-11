// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;
public static class StreamingSKResultExtensions
{
    public static async Task<SKContext> GetFirstChoiceContextAsync(this StreamingSKResult streamingSKResult, CancellationToken cancellationToken = default)
    {
        var choiceContexts = await streamingSKResult.GetChoiceContextsAsync(cancellationToken).ConfigureAwait(false);
        return choiceContexts.First();
    }
}
