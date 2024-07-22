// Copyright (c) Microsoft. All rights reserved.
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Extensions;

internal static class RunPollingOptionsExtensions
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="pollingOptions"></param>
    /// <param name="pollIterationCount"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async static Task WaitAsync(this RunPollingOptions pollingOptions, int pollIterationCount, CancellationToken cancellationToken)
    {
        await Task.Delay(
            pollIterationCount >= 2 ?
                pollingOptions.RunPollingInterval :
                pollingOptions.RunPollingBackoff,
            cancellationToken).ConfigureAwait(false);
    }
}
