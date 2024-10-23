// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Dapr.Actors;
using Dapr.Actors.Runtime;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Runtime;
using Microsoft.VisualStudio.Threading;

namespace Microsoft.SemanticKernel;

internal sealed class ProcessActor : StepActor, IProcess, IDisposable
{
    private const string DaprProcessInfoStateName = "DaprProcessInfo";
    private const string EndStepId = "Microsoft.SemanticKernel.Process.EndStep";
    private readonly JoinableTaskFactory _joinableTaskFactory;
    private readonly JoinableTaskContext _joinableTaskContext;
    private readonly Channel<KernelProcessEvent> _externalEventChannel;

    internal readonly List<IStep> _steps = [];
    internal readonly Kernel _kernel;

    internal List<DaprStepInfo>? _stepsInfos;
    internal DaprProcessInfo? _process;
    private JoinableTask? _processTask;
    private CancellationTokenSource? _processCancelSource;
    private bool _isInitialized;
    private ILogger? _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessActor"/> class.
    /// </summary>
    /// <param name="host">The Dapr host actor</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="loggerFactory">Optional. A <see cref="ILoggerFactory"/>.</param>
    public ProcessActor(ActorHost host, Kernel kernel, ILoggerFactory? loggerFactory)
        : base(host, kernel, loggerFactory)
    {
        this._kernel = kernel;
        this._externalEventChannel = Channel.CreateUnbounded<KernelProcessEvent>();
        this._joinableTaskContext = new JoinableTaskContext();
        this._joinableTaskFactory = new JoinableTaskFactory(this._joinableTaskContext);
    }

    #region Public Actor Methods

    public async Task InitializeProcessAsync(DaprProcessInfo processInfo, string? parentProcessId)
    {
        Verify.NotNull(processInfo);
        Verify.NotNull(processInfo.Steps);

        // Only initialize once. This check is required as the actor can be re-activated from persisted state and
        // this should not result in multiple initializations.
        if (this._isInitialized)
        {
            return;
        }

        // Initialize the process
        await this.Int_InitializeProcessAsync(processInfo, parentProcessId).ConfigureAwait(false);

        // Save the state
        await this.StateManager.AddStateAsync(DaprProcessInfoStateName, processInfo).ConfigureAwait(false);
        await this.StateManager.AddStateAsync("parentProcessId", parentProcessId).ConfigureAwait(false);
        await this.StateManager.AddStateAsync("kernelStepActivated", true).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    public async Task Int_InitializeProcessAsync(DaprProcessInfo processInfo, string? parentProcessId)
    {
        Verify.NotNull(processInfo);
        Verify.NotNull(processInfo.Steps);

        this.ParentProcessId = parentProcessId;
        this._process = processInfo;
        this._stepsInfos = new List<DaprStepInfo>(this._process.Steps);
        this._logger = this.LoggerFactory?.CreateLogger(this._process.State.Name) ?? new NullLogger<StepActor>();

        // Initialize the input and output edges for the process
        this._outputEdges = this._process.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());

        // Initialize the steps within this process
        foreach (var step in this._stepsInfos)
        {
            IStep? stepActor = null;

            // The current step should already have a name.
            Verify.NotNull(step.State?.Name);

            if (step is DaprProcessInfo kernelStep)
            {
                // The process will only have an Id if its already been executed.
                if (string.IsNullOrWhiteSpace(kernelStep.State.Id))
                {
                    kernelStep = kernelStep with { State = kernelStep.State with { Id = Guid.NewGuid().ToString() } };
                }

                // Initialize the step as a process.
                var scopedProcessId = this.ScopedActorId(new ActorId(kernelStep.State.Id!));
                var processActor = this.ProxyFactory.CreateActorProxy<IProcess>(scopedProcessId, nameof(ProcessActor));
                await processActor.InitializeProcessAsync(kernelStep, this.Id.GetId()).ConfigureAwait(false);
                stepActor = this.ProxyFactory.CreateActorProxy<IStep>(scopedProcessId, nameof(ProcessActor));
            }
            else
            {
                // The current step should already have an Id.
                Verify.NotNull(step.State?.Id);

                var scopedStepId = this.ScopedActorId(new ActorId(step.State.Id!));
                stepActor = this.ProxyFactory.CreateActorProxy<IStep>(scopedStepId, nameof(StepActor));
                await stepActor.InitializeStepAsync(step, this.Id.GetId()).ConfigureAwait(false);
            }

            this._steps.Add(stepActor);
        }

        this._isInitialized = true;
    }

    /// <summary>
    /// Starts the process with an initial event and an optional kernel.
    /// </summary>
    /// <param name="keepAlive">Indicates if the process should wait for external events after it's finished processing.</param>
    /// <returns> <see cref="Task"/></returns>
    public Task StartAsync(bool keepAlive)
    {
        if (!this._isInitialized)
        {
            throw new InvalidOperationException("The process cannot be started before it has been initialized.");
        }

        this._processCancelSource = new CancellationTokenSource();
        this._processTask = this._joinableTaskFactory.RunAsync(()
            => this.Internal_ExecuteAsync(this._kernel, keepAlive: keepAlive, cancellationToken: this._processCancelSource.Token));

        return Task.CompletedTask;
    }

    /// <summary>
    /// Starts the process with an initial event and then waits for the process to finish. In this case the process will not
    /// keep alive waiting for external events after the internal messages have stopped.
    /// </summary>
    /// <param name="processEvent">Required. The <see cref="KernelProcessEvent"/> to start the process with.</param>
    /// <returns>A <see cref="Task"/></returns>
    public async Task RunOnceAsync(KernelProcessEvent processEvent)
    {
        Verify.NotNull(processEvent);
        var externalEventQueue = this.ProxyFactory.CreateActorProxy<IExternalEventBuffer>(new ActorId(this.Id.GetId()), nameof(ExternalEventBufferActor));
        await externalEventQueue.EnqueueAsync(processEvent).ConfigureAwait(false);
        await this.StartAsync(keepAlive: false).ConfigureAwait(false);
        await this._processTask!.JoinAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Stops a running process. This will cancel the process and wait for it to complete before returning.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
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

    /// <summary>
    /// Sends a message to the process. This does not start the process if it's not already running, in
    /// this case the message will remain queued until the process is started.
    /// </summary>
    /// <param name="processEvent">Required. The <see cref="KernelProcessEvent"/> to start the process with.</param>
    /// <returns>A <see cref="Task"/></returns>
    public async Task SendMessageAsync(KernelProcessEvent processEvent)
    {
        Verify.NotNull(processEvent);
        await this._externalEventChannel.Writer.WriteAsync(processEvent).ConfigureAwait(false);
    }

    /// <summary>
    /// Gets the process information.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    public async Task<DaprProcessInfo> GetProcessInfoAsync()
    {
        return await this.ToDaprProcessInfoAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// When the process is used as a step within another process, this method will be called
    /// rather than ToKernelProcessAsync when extracting the state.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public override async Task<DaprStepInfo> ToDaprStepInfoAsync()
    {
        return await this.ToDaprProcessInfoAsync().ConfigureAwait(false);
    }

    protected override async Task OnActivateAsync()
    {
        var existingProcessInfo = await this.StateManager.TryGetStateAsync<DaprProcessInfo>(DaprProcessInfoStateName).ConfigureAwait(false);
        if (existingProcessInfo.HasValue)
        {
            this.ParentProcessId = await this.StateManager.GetStateAsync<string>("parentProcessId").ConfigureAwait(false);
            await this.Int_InitializeProcessAsync(existingProcessInfo.Value, this.ParentProcessId).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// The name of the step.
    /// </summary>
    protected override string Name => this._process?.State.Name ?? throw new KernelException("The Process must be initialized before accessing the Name property.");

    #endregion

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
            this._logger?.LogError("{ErrorMessage}", errorMessage);
            throw new KernelException(errorMessage);
        }

        string eventId = message.TargetEventId!;
        if (this._outputEdges!.TryGetValue(eventId, out List<KernelProcessEdge>? edges) && edges is not null)
        {
            foreach (var edge in edges)
            {
                // Create the external event that will be used to start the nested process. Since this event came
                // from outside this processes, we set the visibility to internal so that it's not emitted back out again.
                var nestedEvent = new KernelProcessEvent() { Id = eventId, Data = message.TargetEventData, Visibility = KernelProcessEventVisibility.Internal };

                // Run the nested process completely within a single superstep.
                await this.RunOnceAsync(nestedEvent).ConfigureAwait(false);
            }
        }
    }

    #region Private Methods

    /// <summary>
    /// Initializes this process as a step within another process.
    /// </summary>
    /// <returns>A <see cref="ValueTask"/></returns>
    /// <exception cref="KernelException"></exception>
    protected override ValueTask ActivateStepAsync()
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
            for (int superstep = 0; superstep < maxSupersteps; superstep++)
            {
                // Check for EndStep messages. If there are any then cancel the process.
                if (await this.IsEndMessageSentAsync().ConfigureAwait(false))
                {
                    this._processCancelSource?.Cancel();
                    break;
                }

                // Check for external events
                await this.EnqueueExternalMessagesAsync().ConfigureAwait(false);

                // Reach out to all of the steps in the process and instruct them to retrieve their pending messages from their associated queues.
                var stepPreparationTasks = this._steps.Select(step => step.PrepareIncomingMessagesAsync()).ToList();
                var messageCounts = await Task.WhenAll(stepPreparationTasks).ConfigureAwait(false);

                // If there are no messages to process, wait for an external event or finish.
                if (messageCounts.Sum() == 0)
                {
                    if (!keepAlive || !await this._externalEventChannel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false))
                    {
                        this._processCancelSource?.Cancel();
                        break;
                    }
                }

                // Process the incoming messages for each step.
                var stepProcessingTasks = this._steps.Select(step => step.ProcessIncomingMessagesAsync()).ToList();
                await Task.WhenAll(stepProcessingTasks).ConfigureAwait(false);

                // Handle public events that need to be bubbled out of the process.
                var eventQueue = this.ProxyFactory.CreateActorProxy<IEventBuffer>(new ActorId(this.Id.GetId()), nameof(EventBufferActor));
                var allEvents = await eventQueue.DequeueAllAsync().ConfigureAwait(false);
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
    private async Task EnqueueExternalMessagesAsync()
    {
        var externalEventQueue = this.ProxyFactory.CreateActorProxy<IExternalEventBuffer>(new ActorId(this.Id.GetId()), nameof(ExternalEventBufferActor));
        var externalEvents = await externalEventQueue.DequeueAllAsync().ConfigureAwait(false);

        foreach (var externalEvent in externalEvents)
        {
            if (this._outputEdges!.TryGetValue(externalEvent.Id!, out List<KernelProcessEdge>? edges) && edges is not null)
            {
                foreach (var edge in edges)
                {
                    ProcessMessage message = ProcessMessageFactory.CreateFromEdge(edge, externalEvent.Data);
                    var scopedMessageBufferId = this.ScopedActorId(new ActorId(edge.OutputTarget.StepId));
                    var messageQueue = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(scopedMessageBufferId, nameof(MessageBufferActor));
                    await messageQueue.EnqueueAsync(message).ConfigureAwait(false);
                }
            }
        }
    }

    /// <summary>
    /// Determines is the end message has been sent to the process.
    /// </summary>
    /// <returns>True if the end message has been sent, otherwise false.</returns>
    private async Task<bool> IsEndMessageSentAsync()
    {
        var scopedMessageBufferId = this.ScopedActorId(new ActorId(EndStepId));
        var endMessageQueue = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(scopedMessageBufferId, nameof(MessageBufferActor));
        var messages = await endMessageQueue.DequeueAllAsync().ConfigureAwait(false);
        return messages.Count > 0;
    }

    /// <summary>
    /// Builds a <see cref="KernelProcess"/> from the current <see cref="ProcessActor"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    /// <exception cref="InvalidOperationException"></exception>
    private async Task<DaprProcessInfo> ToDaprProcessInfoAsync()
    {
        var processState = new KernelProcessState(this.Name, this.Id.GetId());
        var stepTasks = this._steps.Select(step => step.ToDaprStepInfoAsync()).ToList();
        var steps = await Task.WhenAll(stepTasks).ConfigureAwait(false);
        return new DaprProcessInfo { InnerStepDotnetType = this._process!.InnerStepDotnetType, Edges = this._process!.Edges, State = processState, Steps = steps.ToList() };
    }

    /// <summary>
    /// Scopes the Id of a step within the process to the process.
    /// </summary>
    /// <param name="actorId">The actor Id to scope.</param>
    /// <returns>A new <see cref="ActorId"/> which is scoped to the process.</returns>
    private ActorId ScopedActorId(ActorId actorId)
    {
        return new ActorId($"{this.Id}.{actorId.GetId()}");
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
