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
    private CancellationTokenSource? _processCancelSource;
    private readonly JoinableTaskFactory _joinableTaskFactory;
    private readonly JoinableTaskContext _joinableTaskContext;
    private readonly Channel<KernelProcessEvent> _externalEventChannel;

    internal readonly List<KernelProcessStepInfo> _stepsInfos;
    internal readonly List<LocalStep> _steps;
    internal readonly KernelProcess _process;
    internal readonly Kernel _kernel;

    private readonly ILogger? _logger;
    private JoinableTask? _processTask;

    /// <summary>
    /// Initializes a new instance of the <see cref="LocalProcess"/> class.
    /// </summary>
    /// <param name="process">The <see cref="KernelProcess"/> instance.</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="parentProcessId">Optional. The Id of the parent process if one exists, otherwise null.</param>
    /// <param name="loggerFactory">Optional. A <see cref="ILoggerFactory"/>.</param>
    public LocalProcess(KernelProcess process, Kernel kernel, string? parentProcessId = null, ILoggerFactory? loggerFactory = null)
        : base(process.State.Name!, process.State.Id ?? Guid.NewGuid().ToString("n"), kernel, parentProcessId, loggerFactory)
    {
        Verify.NotNull(process);
        Verify.NotNull(process.Steps);
        Verify.NotNull(kernel);

        this._stepsInfos = new List<KernelProcessStepInfo>(process.Steps);
        this._steps = [];
        this._kernel = kernel;
        this._process = process;
        this._externalEventChannel = Channel.CreateUnbounded<KernelProcessEvent>();
        this._joinableTaskContext = new JoinableTaskContext();
        this._joinableTaskFactory = new JoinableTaskFactory(this._joinableTaskContext);
        this._logger = this.LoggerFactory?.CreateLogger(this.Name) ?? new NullLogger<LocalStep>();
    }

    /// <summary>
    /// Loads the process and initializes the steps. Once this is complete the process can be started.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    public async Task LoadAsync()
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
                    name: step.State.Name,
                    id: step.State.Id,
                    kernel: this._kernel,
                    parentProcessId: this.Id,
                    loggerFactory: this.LoggerFactory);
            }

            await localStep.InitializeAsync(step).ConfigureAwait(false);
            this._steps.Add(localStep);
        }
    }

    /// <summary>
    /// Starts the process with an initial event and an optional kernel.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> instance to use within the running process.</param>
    /// <param name="keepAlive">Indicates if the process should wait for external events after it's finished processing.</param>
    /// <returns> <see cref="Task"/></returns>
    public Task StartAsync(Kernel? kernel = null, bool keepAlive = true)
    {
        this._processCancelSource = new CancellationTokenSource();
        this._processTask = this._joinableTaskFactory.RunAsync(()
            => this.Internal_ExecuteAsync(kernel, keepAlive: keepAlive, cancellationToken: this._processCancelSource.Token));
        return Task.CompletedTask;
    }

    public async Task RunOnceAsync(KernelProcessEvent? processEvent, Kernel? kernel = null)
    {
        Verify.NotNull(processEvent);
        await this._externalEventChannel.Writer.WriteAsync(processEvent).ConfigureAwait(false);
        await this.StartAsync(kernel, keepAlive: false).ConfigureAwait(false);
        await this._processTask!.JoinAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Stops a running process. This will cancel the process and wait for it to complete before returning.
    /// </summary>
    /// <returns></returns>
    public async Task StopAsync()
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

    public async Task SendMessageAsync(KernelProcessEvent? processEvent, Kernel? kernel = null)
    {
        Verify.NotNull(processEvent);
        await this._externalEventChannel.Writer.WriteAsync(processEvent).ConfigureAwait(false);
    }

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
                this.EnqueueExternalEventsAsync(messageChannel);

                // Get all of the messages that have been sent to the steps within the process and queue them up for processing.
                foreach (var step in this._steps)
                {
                    this.EnqueueStepMessagesAsync(step, localKernel, messageChannel);
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

    private void EnqueueExternalEventsAsync(Queue<LocalMessage> stepQueue)
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
                    stepQueue.Enqueue(newMessage);
                }
            }
        }
    }

    private void EnqueueStepMessagesAsync(LocalStep step, Kernel kernel, Queue<LocalMessage> messageChannel)
    {
        // Process all of the messages that have been sent to this step
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

    public void Dispose()
    {
        this._externalEventChannel.Writer.Complete();
        this._joinableTaskContext.Dispose();
        this._joinableTaskContext.Dispose();
        this._processCancelSource?.Dispose();
    }
}
