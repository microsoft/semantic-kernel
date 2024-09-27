// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.VisualStudio.Threading;

namespace Microsoft.SemanticKernel;

internal sealed class LocalProcess : LocalStep, IDisposable
{
    private const string EndProcessId = "END";
    private readonly JoinableTaskFactory _joinableTaskFactory;
    private readonly JoinableTaskContext _joinableTaskContext;
    private readonly Channel<KernelProcessEvent> _externalEventChannel;
    private readonly Lazy<ValueTask> _initializeTask;

    internal readonly List<KernelProcessStepInfo> _stepsInfos;
    internal readonly List<LocalStep> _steps = [];
    internal readonly KernelProcess _process;
    internal readonly Kernel _kernel;

    private readonly ILogger? _logger;
    private JoinableTask? _processTask;
    private CancellationTokenSource? _processCancelSource;

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalProcess"/> class.
    /// </summary>
    /// <param name="process">The <see cref="KernelProcess"/> instance.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="parentProcessId">Optional. The Id of the parent process if one exists, otherwise null.</param>
    /// <param name="loggerFactory">Optional. A <see cref="ILoggerFactory"/>.</param>
    internal LocalProcess(KernelProcess process, Kernel kernel, string? parentProcessId = null, ILoggerFactory? loggerFactory = null)
        : base(process, kernel, parentProcessId, loggerFactory)
    {
        Verify.NotNull(process);
        Verify.NotNull(process.Steps);
        Verify.NotNull(kernel);

        this._stepsInfos = new List<KernelProcessStepInfo>(process.Steps);
        this._kernel = kernel;
        this._process = process;
        this._initializeTask = new Lazy<ValueTask>(this.InitializeProcessAsync);
        this._externalEventChannel = Channel.CreateUnbounded<KernelProcessEvent>();
        this._joinableTaskContext = new JoinableTaskContext();
        this._joinableTaskFactory = new JoinableTaskFactory(this._joinableTaskContext);
        this._logger = this.LoggerFactory?.CreateLogger(this.Name) ?? new NullLogger<LocalStep>();
    }

    /// <summary>
    /// Starts the process with an initial event and an optional kernel.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> instance to use within the running process.</param>
    /// <param name="keepAlive">Indicates if the process should wait for external events after it's finished processing.</param>
    /// <returns> <see cref="Task"/></returns>
    internal async Task StartAsync(Kernel? kernel = null, bool keepAlive = true)
    {
        // Lazy one-time initialization of the process before staring it.
        await this._initializeTask.Value.ConfigureAwait(false);

        this._processCancelSource = new CancellationTokenSource();
        this._processTask = this._joinableTaskFactory.RunAsync(()
            => this.Internal_ExecuteAsync(kernel, keepAlive: keepAlive, cancellationToken: this._processCancelSource.Token));
    }

    /// <summary>
    /// Starts the process with an initial event and then waits for the process to finish. In this case the process will not
    /// keep alive waiting for external events after the internal messages have stopped.
    /// </summary>
    /// <param name="processEvent">Required. The <see cref="KernelProcessEvent"/> to start the process with.</param>
    /// <param name="kernel">Optional. A <see cref="Kernel"/> to use when executing the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    internal async Task RunOnceAsync(KernelProcessEvent? processEvent, Kernel? kernel = null)
    {
        Verify.NotNull(processEvent);
        await this._externalEventChannel.Writer.WriteAsync(processEvent).ConfigureAwait(false);
        await this.StartAsync(kernel, keepAlive: false).ConfigureAwait(false);
        await this._processTask!.JoinAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Stops a running process. This will cancel the process and wait for it to complete before returning.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    internal async Task StopAsync()
    {
        if (this._processTask is null || this._processCancelSource is null || this._processTask.IsCompleted)
        {
            return;
        }

        // Cancel the process and wait for it to complete.
        this._processCancelSource.Cancel();

        try
        {
            await this._processTask;
        }
        catch (OperationCanceledException)
        {
            // The task was cancelled, so we can ignore this exception.
        }
        finally
        {
            this._processCancelSource.Dispose();
        }
    }

    /// <summary>
    /// Sends a message to the process. This does not start the process if it's not already running, in
    /// this case the message will remain queued until the process is started.
    /// </summary>
    /// <param name="processEvent">Required. The <see cref="KernelProcessEvent"/> to start the process with.</param>
    /// <param name="kernel">Optional. A <see cref="Kernel"/> to use when executing the process.</param>
    /// <returns>A <see cref="Task"/></returns>
    internal async Task SendMessageAsync(KernelProcessEvent processEvent, Kernel? kernel = null)
    {
        Verify.NotNull(processEvent);
        await this._externalEventChannel.Writer.WriteAsync(processEvent).ConfigureAwait(false);
    }

    #region Private Methods

    /// <summary>
    /// Loads the process and initializes the steps. Once this is complete the process can be started.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    private ValueTask InitializeProcessAsync()
    {
        // Initialize the input and output edges for the process
        this._outputEdges = this._process.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());

        // Initialize the steps within this process
        foreach (var step in this._stepsInfos)
        {
            LocalStep? localStep = null;

            // The current step should already have a name.
            Verify.NotNull(step.State?.Name);

            if (step is KernelProcess kernelStep)
            {
                // The process will only have an Id if its already been executed.
                if (string.IsNullOrWhiteSpace(kernelStep.State.Id))
                {
                    kernelStep = kernelStep with { State = kernelStep.State with { Id = Guid.NewGuid().ToString() } };
                }

                var process = new LocalProcess(
                    process: kernelStep,
                    kernel: this._kernel,
                    parentProcessId: this.Id,
                    loggerFactory: this.LoggerFactory);

                localStep = process;
            }
            else
            {
                // The current step should already have an Id.
                Verify.NotNull(step.State?.Id);

                localStep = new LocalStep(
                    stepInfo: step,
                    kernel: this._kernel,
                    parentProcessId: this.Id,
                    loggerFactory: this.LoggerFactory);
            }

            this._steps.Add(localStep);
        }

        return default;
    }

    /// <summary>
    /// Executes the process asynchronously until one of the following conditions is met:
    /// - The process has been cancelled.
    /// - The process has hit the specified limit of supersteps.
    /// - There are no more messages to be process AND <paramref name="keepAlive"/> is false. No more messages means that
    /// none of the steps in this process emitted any events in the last superstep, indicating that they have finished processing.
    /// </summary>
    /// <param name="kernel">An options override of the process level kernel.</param>
    /// <param name="maxSupersteps">The maximum number of supersteps that this process can execute. Defaults to 100.</param>
    /// <param name="keepAlive">If true, the process will continue running after internal events have stopped. This allows the process to wait for external events.</param>
    /// <param name="cancellationToken">A <see cref="CancellationToken"/></param>
    /// <returns></returns>
    private async Task Internal_ExecuteAsync(Kernel? kernel = null, int maxSupersteps = 100, bool keepAlive = true, CancellationToken cancellationToken = default)
    {
        Kernel localKernel = kernel ?? this._kernel;
        Queue<LocalMessage> messageChannel = new();

        try
        {
            // Run the Pregel algorithm until there are no more messages being sent.
            LocalStep? finalStep = null;
            for (int superstep = 0; superstep < maxSupersteps; superstep++)
            {
                // Check for external events
                this.EnqueueExternalMessages(messageChannel);

                // Get all of the messages that have been sent to the steps within the process and queue them up for processing.
                foreach (var step in this._steps)
                {
                    this.EnqueueStepMessages(step, messageChannel);
                }

                // Complete the writing side, indicating no more messages in this superstep.
                var messagesToProcess = messageChannel.ToList();
                messageChannel.Clear();

                // If there are no messages to process, wait for an external event.
                if (messagesToProcess.Count == 0)
                {
                    if (!keepAlive || !await this._externalEventChannel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false))
                    {
                        this._processCancelSource?.Cancel();
                        break;
                    }
                }

                List<Task> messageTasks = [];
                foreach (var message in messagesToProcess)
                {
                    // Check for end condition
                    if (message.DestinationId.Equals(EndProcessId, StringComparison.OrdinalIgnoreCase))
                    {
                        this._processCancelSource?.Cancel();
                        break;
                    }

                    var destinationStep = this._steps.First(v => v.Id == message.DestinationId);

                    // Send a message to the step
                    messageTasks.Add(destinationStep.HandleMessageAsync(message));
                    finalStep = destinationStep;
                }

                await Task.WhenAll(messageTasks).ConfigureAwait(false);
            }
        }
        catch (Exception ex)
        {
            this._logger?.LogError("An error occurred while running the process: {ErrorMessage}.", ex.Message);
            throw;
        }
        finally
        {
            if (this._processCancelSource?.IsCancellationRequested ?? false)
            {
                this._processCancelSource.Cancel();
            }

            this._processCancelSource?.Dispose();
        }

        return;
    }

    /// <summary>
    /// Processes external events that have been sent to the process, translates them to <see cref="LocalMessage"/>s, and enqueues
    /// them to the provided message channel so that they can be processesed in the next superstep.
    /// </summary>
    /// <param name="messageChannel">The message channel where messages should be enqueued.</param>
    private void EnqueueExternalMessages(Queue<LocalMessage> messageChannel)
    {
        while (this._externalEventChannel.Reader.TryRead(out var externalEvent))
        {
            if (this._outputEdges!.TryGetValue(externalEvent.Id!, out List<KernelProcessEdge>? edges) && edges is not null)
            {
                foreach (var edge in edges)
                {
                    Dictionary<string, object?> parameterValue = new();
                    if (!string.IsNullOrWhiteSpace(edge.OutputTarget.ParameterName))
                    {
                        parameterValue.Add(edge.OutputTarget.ParameterName!, externalEvent.Data);
                    }

                    LocalMessage newMessage = new(edge.SourceStepId, edge.OutputTarget.StepId, edge.OutputTarget.FunctionName, parameterValue);
                    messageChannel.Enqueue(newMessage);
                }
            }
        }
    }

    /// <summary>
    /// Processes events emitted by the given step in the last superstep, translates them to <see cref="LocalMessage"/>s, and enqueues
    /// them to the provided message channel so that they can be processesed in the next superstep.
    /// </summary>
    /// <param name="step">The step containing outgoing events to process.</param>
    /// <param name="messageChannel">The message channel where messages should be enqueued.</param>
    private void EnqueueStepMessages(LocalStep step, Queue<LocalMessage> messageChannel)
    {
        var allStepEvents = step.GetAllEvents();
        foreach (var stepEvent in allStepEvents)
        {
            foreach (var edge in step.GetEdgeForEvent(stepEvent.Id!))
            {
                var target = edge.OutputTarget;
                Dictionary<string, object?> parameterValue = new();
                if (!string.IsNullOrWhiteSpace(target.ParameterName))
                {
                    parameterValue.Add(target.ParameterName!, stepEvent.Data);
                }

                LocalMessage newMessage = new(edge.SourceStepId, target.StepId, target.FunctionName, parameterValue);
                messageChannel.Enqueue(newMessage);
            }
        }
    }

    #endregion

    public void Dispose()
    {
        this._externalEventChannel.Writer.Complete();
        this._joinableTaskContext.Dispose();
        this._joinableTaskContext.Dispose();
        this._processCancelSource?.Dispose();
    }
}
