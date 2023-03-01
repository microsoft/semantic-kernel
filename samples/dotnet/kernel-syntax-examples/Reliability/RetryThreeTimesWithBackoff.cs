// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Reliability;
using Polly;
using Polly.Retry;

namespace Reliability;

/// <summary>
/// An example of a retry mechanism that retries three times with backoff.
/// </summary>
public class RetryThreeTimesWithBackoff : IRetryMechanism
{
    public Task ExecuteWithRetryAsync(Func<Task> action, ILogger log, CancellationToken cancellationToken = default)
    {
        var policy = GetPolicy(log);
        return policy.ExecuteAsync((_) => action(), cancellationToken);
    }

    private static AsyncRetryPolicy GetPolicy(ILogger log)
    {
        return Policy
            .Handle<AIException>(ex => ex.ErrorCode == AIException.ErrorCodes.Throttling)
            .WaitAndRetryAsync(new[]
                {
                    TimeSpan.FromSeconds(2),
                    TimeSpan.FromSeconds(4),
                    TimeSpan.FromSeconds(8)
                },
                (ex, timespan, retryCount, _) => log.LogWarning(ex,
                    "Error executing action [attempt {0} of ], pausing {1} msecs", retryCount, timespan.TotalMilliseconds));
    }
}
