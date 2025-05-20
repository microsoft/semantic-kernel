// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Represents the result of an orchestration operation that yields a value of type <typeparamref name="TValue"/>.
/// This class encapsulates the asynchronous completion of an orchestration process.
/// </summary>
/// <typeparam name="TValue">The type of the value produced by the orchestration.</typeparam>
public sealed class OrchestrationResult<TValue> : IDisposable
{
    private readonly OrchestrationContext _context;
    private readonly CancellationTokenSource _cancelSource;
    private readonly TaskCompletionSource<TValue> _completion;
    private readonly ILogger _logger;
    private bool _isDisposed;

    internal OrchestrationResult(OrchestrationContext context, TaskCompletionSource<TValue> completion, CancellationTokenSource orchestrationCancelSource, ILogger logger)
    {
        this._cancelSource = orchestrationCancelSource;
        this._context = context;
        this._completion = completion;
        this._logger = logger;
    }

    /// <summary>
    /// Releases all resources used by the <see cref="OrchestrationResult{TValue}"/> instance.
    /// </summary>
    public void Dispose()
    {
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Gets the orchestration name associated with this orchestration result.
    /// </summary>
    public string Orchestration => this._context.Orchestration;

    /// <summary>
    /// Gets the topic identifier associated with this orchestration result.
    /// </summary>
    public TopicId Topic => this._context.Topic;

    /// <summary>
    /// Asynchronously retrieves the orchestration result value.
    /// If a timeout is specified, the method will throw a <see cref="TimeoutException"/>
    /// if the orchestration does not complete within the allotted time.
    /// </summary>
    /// <param name="timeout">An optional <see cref="TimeSpan"/> representing the maximum wait duration.</param>
    /// <param name="cancellationToken">A cancellation token that can be used to cancel the operation.</param>
    /// <returns>A <see cref="ValueTask{TValue}"/> representing the result of the orchestration.</returns>
    /// <exception cref="ObjectDisposedException">Thrown if this instance has been disposed.</exception>
    /// <exception cref="TimeoutException">Thrown if the orchestration does not complete within the specified timeout period.</exception>
    public async ValueTask<TValue> GetValueAsync(TimeSpan? timeout = null, CancellationToken cancellationToken = default)
    {
#if !NETCOREAPP
        if (this._isDisposed)
        {
            throw new ObjectDisposedException(this.GetType().Name);
        }
#else
        ObjectDisposedException.ThrowIf(this._isDisposed, this);
#endif

        this._logger.LogOrchestrationResultAwait(this.Orchestration, this.Topic);

        if (timeout.HasValue)
        {
            Task[] tasks = { this._completion.Task };
            if (!Task.WaitAll(tasks, timeout.Value))
            {
                this._logger.LogOrchestrationResultTimeout(this.Orchestration, this.Topic);
                throw new TimeoutException($"Orchestration did not complete within the allowed duration ({timeout}).");
            }
        }

        this._logger.LogOrchestrationResultComplete(this.Orchestration, this.Topic);

        return await this._completion.Task.ConfigureAwait(false);
    }

    /// <summary>
    /// Cancel the orchestration associated with this result.
    /// </summary>
    /// <exception cref="ObjectDisposedException">Thrown if this instance has been disposed.</exception>
    /// <remarks>
    /// Cancellation is not expected to immediately halt the orchestration.  Messages that
    /// are already in-flight may still be processed.
    /// </remarks>
    public void Cancel()
    {
#if !NETCOREAPP
        if (this._isDisposed)
        {
            throw new ObjectDisposedException(this.GetType().Name);
        }
#else
        ObjectDisposedException.ThrowIf(this._isDisposed, this);
#endif

        this._logger.LogOrchestrationResultCancelled(this.Orchestration, this.Topic);
        this._cancelSource.Cancel();
        this._completion.SetCanceled();
    }

    private void Dispose(bool disposing)
    {
        if (!this._isDisposed)
        {
            if (disposing)
            {
                this._cancelSource.Dispose();
            }

            this._isDisposed = true;
        }
    }
}
