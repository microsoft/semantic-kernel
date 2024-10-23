// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Runtime;
using Microsoft.VisualStudio.Threading;

namespace Microsoft.SemanticKernel;

internal sealed class LocalProcess : LocalStep, IDisposable
{
    private const string EndProcessId = "Microsoft.SemanticKernel.Process.EndStep";
    private readonly JoinableTaskFactory _joinableTaskFactory;
    private readonly JoinableTaskContext _joinableTaskContext;
    private readonly Channel<KernelProcessEvent> _externalEventChannel;
    private readonly Lazy<ValueTask> _initializeTask;

    internal readonly List<KernelProcessStepInfo> _stepsInfos;
    internal readonly List<LocalStep> _steps = [];
    internal readonly KernelProcess _process;
    internal readonly Kernel _kernel;

    private readonly ILogger _logger;
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

    /// <summary>
    /// Gets the process information.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    internal async Task<KernelProcess> GetProcessInfoAsync()
    {
        return await this.ToKernelProcessAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Handles a <see cref="ProcessMessage"/> that has been sent to the process. This happens only in the case
    /// of a process (this one) running as a step within another process (this one's parent). In this case the
    /// entire sub-process should be executed within a single superstep.
    /// </summary>
    /// <param name="message">The message to process.</param>
    /// <returns>A <see cref="Task"/></returns>
    /// <exception cref="KernelException"></exception>
    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        if (string.IsNullOrWhiteSpace(message.TargetEventId))
        {
            string errorMessage = "Internal Process Error: The target event id must be specified when sending a message to a step.";
            this._logger.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        string eventId = message.TargetEventId!;
        if (this._outputEdges!.TryGetValue(eventId, out List<KernelProcessEdge>? edges) && edges is not null)
        {
            // Create the external event that will be used to start the nested process. Since this event came
            // from outside this processes, we set the visibility to internal so that it's not emitted back out again.
            var nestedEvent = new KernelProcessEvent() { Id = eventId, Data = message.TargetEventData, Visibility = KernelProcessEventVisibility.Internal };

            // Run the nested process completely within a single superstep.
            await this.RunOnceAsync(nestedEvent, this._kernel).ConfigureAwait(false);
        }
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

                //await process.StartAsync(kernel: this._kernel, keepAlive: true).ConfigureAwait(false);
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
    /// Initializes this process as a step within another process.
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    /// <exception cref="KernelException"></exception>
    protected override ValueTask InitializeStepAsync()
    {
        // The process does not need any further initialization as it's already been initialized.
        // Override the base method to prevent it from being called.
        return default;
    }

    private async Task Internal_ExecuteAsync(Kernel? kernel = null, int maxSupersteps = 100, bool keepAlive = true, CancellationToken cancellationToken = default)
    {
        Kernel localKernel = kernel ?? this._kernel;
        Queue<ProcessMessage> messageChannel = new();

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
    /// Processes external events that have been sent to the process, translates them to <see cref="ProcessMessage"/>s, and enqueues
    /// them to the provided message channel so that they can be processed in the next superstep.
    /// </summary>
    /// <param name="messageChannel">The message channel where messages should be enqueued.</param>
    private void EnqueueExternalMessages(Queue<ProcessMessage> messageChannel)
    {
        while (this._externalEventChannel.Reader.TryRead(out var externalEvent))
        {
            if (this._outputEdges!.TryGetValue(externalEvent.Id!, out List<KernelProcessEdge>? edges) && edges is not null)
            {
                foreach (var edge in edges)
                {
                    ProcessMessage message = ProcessMessageFactory.CreateFromEdge(edge, externalEvent.Data);
                    messageChannel.Enqueue(message);
                }
            }
        }
    }

    /// <summary>
    /// Processes events emitted by the given step in the last superstep, translates them to <see cref="ProcessMessage"/>s, and enqueues
    /// them to the provided message channel so that they can be processed in the next superstep.
    /// </summary>
    /// <param name="step">The step containing outgoing events to process.</param>
    /// <param name="messageChannel">The message channel where messages should be enqueued.</param>
    private void EnqueueStepMessages(LocalStep step, Queue<ProcessMessage> messageChannel)
    {
        var allStepEvents = step.GetAllEvents();
        foreach (var stepEvent in allStepEvents)
        {
            // Emit the event out of the process (this one) if it's visibility is public.
            if (stepEvent.Visibility == KernelProcessEventVisibility.Public)
            {
                base.EmitEvent(stepEvent);
            }

            // Get the edges for the event and queue up the messages to be sent to the next steps.
            foreach (var edge in step.GetEdgeForEvent(stepEvent.Id!))
            {
                ProcessMessage message = ProcessMessageFactory.CreateFromEdge(edge, stepEvent.Data);
                messageChannel.Enqueue(message);
            }
        }
    }

    /// <summary>
    /// Builds a <see cref="KernelProcess"/> from the current <see cref="LocalProcess"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    /// <exception cref="InvalidOperationException"></exception>
    private async Task<KernelProcess> ToKernelProcessAsync()
    {
        var processState = new KernelProcessState(this.Name, this.Id);
        var stepTasks = this._steps.Select(step => step.ToKernelProcessStepInfoAsync()).ToList();
        var steps = await Task.WhenAll(stepTasks).ConfigureAwait(false);
        return new KernelProcess(processState, steps, this._outputEdges);
    }

    /// <summary>
    /// When the process is used as a step within another process, this method will be called
    /// rather than ToKernelProcessAsync when extracting the state.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    internal override async Task<KernelProcessStepInfo> ToKernelProcessStepInfoAsync()
    {
        return await this.ToKernelProcessAsync().ConfigureAwait(false);
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
