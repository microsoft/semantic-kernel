// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Reliability;

/// <summary>
/// A retry mechanism that does not retry.
/// </summary>
internal class PassThroughWithoutRetry : IRetryMechanism
{
    public async Task ExecuteWithRetryAsync(Func<Task> action, ILogger log, CancellationToken cancellationToken = default)
    {
        try
        {
            if (!cancellationToken.IsCancellationRequested)
            {
                await action();
            }
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            log.LogWarning(ex, "Error executing action, not retrying");
            throw;
        }
    }
}
