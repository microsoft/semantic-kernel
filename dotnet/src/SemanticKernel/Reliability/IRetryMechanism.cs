// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Reliability;

/// <summary>
/// Interface for retry mechanisms on AI calls.
/// </summary>
public interface IRetryMechanism
{
    /// <summary>
    /// Executes the given action with retry logic.
    /// </summary>
    /// <param name="action">The action to retry on exception.</param>
    /// <param name="log">The logger to use.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>An awaitable task.</returns>
    Task ExecuteWithRetryAsync(Func<Task> action, ILogger log, CancellationToken cancellationToken = default);
}
