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
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;
using Microsoft.SemanticKernel.Process.Serialization;
using Microsoft.VisualStudio.Threading;

namespace Microsoft.SemanticKernel;

internal sealed class ProcessActor : StepActor, IProcess, IDisposable
{
    private readonly JoinableTaskFactory _joinableTaskFactory;
    private readonly JoinableTaskContext _joinableTaskContext;
    private readonly Channel<KernelProcessEvent> _externalEventChannel;

    internal readonly List<IStep> _steps = [];

    internal IList<DaprStepInfo>? _stepsInfos;
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
    public ProcessActor(ActorHost host, Kernel kernel)
        : base(host, kernel)
    {
        this._externalEventChannel = Channel.CreateUnbounded<KernelProcessEvent>();
        this._joinableTaskContext = new JoinableTaskContext();
        this._joinableTaskFactory = new JoinableTaskFactory(this._joinableTaskContext);
    }

    #region Public Actor Methods

    public async Task InitializeProcessAsync(DaprProcessInfo processInfo, string? parentProcessId, string? eventProxyStepId = null)
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
        await this.InitializeProcessActorAsync(processInfo, parentProcessId, eventProxyStepId).ConfigureAwait(false);

        // Save the state
        await this.StateManager.AddStateAsync(ActorStateKeys.ProcessInfoState, processInfo).ConfigureAwait(false);
        await this.StateManager.AddStateAsync(ActorStateKeys.StepParentProcessId, parentProcessId).ConfigureAwait(false);
        await this.StateManager.AddStateAsync(ActorStateKeys.StepActivatedState, true).ConfigureAwait(false);
        if (!string.IsNullOrWhiteSpace(eventProxyStepId))
        {
            await this.StateManager.AddStateAsync(ActorStateKeys.EventProxyStepId, eventProxyStepId).ConfigureAwait(false);
        }
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
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
            throw new InvalidOperationException("The process cannot be started before it has been initialized.").Log(this._logger);
        }

        this._processCancelSource = new CancellationTokenSource();
        this._processTask = this._joinableTaskFactory.RunAsync(()
            => this.Internal_ExecuteAsync(keepAlive: keepAlive, cancellationToken: this._processCancelSource.Token));

        return Task.CompletedTask;
    }

    /// <summary>
    /// Starts the process with an initial event and then waits for the process to finish. In this case the process will not
    /// keep alive waiting for external events after the internal messages have stopped.
    /// </summary>
    /// <param name="processEvent">Required. The <see cref="KernelProcessEvent"/> to start the process with.</param>
    /// <returns>A <see cref="Task"/></returns>
    public async Task RunOnceAsync(string processEvent)
    {
        Verify.NotNull(processEvent, nameof(processEvent));
        IExternalEventBuffer externalEventQueue = this.ProxyFactory.CreateActorProxy<IExternalEventBuffer>(new ActorId(this.Id.GetId()), nameof(ExternalEventBufferActor));
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
    public async Task SendMessageAsync(string processEvent)
    {
        Verify.NotNull(processEvent, nameof(processEvent));
        await this._externalEventChannel.Writer.WriteAsync(processEvent.ToKernelProcessEvent()).ConfigureAwait(false);
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
    /// <returns>A <see cref="Task{DaprStepInfo}"/></returns>
    public override async Task<DaprStepInfo> ToDaprStepInfoAsync()
    {
        return await this.ToDaprProcessInfoAsync().ConfigureAwait(false);
    }

    protected override async Task OnActivateAsync()
    {
        var existingProcessInfo = await this.StateManager.TryGetStateAsync<DaprProcessInfo>(ActorStateKeys.ProcessInfoState).ConfigureAwait(false);
        if (existingProcessInfo.HasValue)
        {
            this.ParentProcessId = await this.StateManager.GetStateAsync<string>(ActorStateKeys.StepParentProcessId).ConfigureAwait(false);
            string? eventProxyStepId = null;
            if (await this.StateManager.ContainsStateAsync(ActorStateKeys.EventProxyStepId).ConfigureAwait(false))
            {
                eventProxyStepId = await this.StateManager.GetStateAsync<string>(ActorStateKeys.EventProxyStepId).ConfigureAwait(false);
            }
            await this.InitializeProcessActorAsync(existingProcessInfo.Value, this.ParentProcessId, eventProxyStepId).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// The name of the step.
    /// </summary>
    protected override string Name => this._process?.State.Name ?? throw new KernelException("The Process must be initialized before accessing the Name property.").Log(this._logger);

    #endregion

    /// <summary>
    /// Handles a <see cref="ProcessMessage"/> that has been sent to the process. This happens only in the case
    /// of a process (this one) running as a step within another process (this one's parent). In this case the
    /// entire sub-process should be executed within a single superstep.
    /// </summary>
    /// <param name="message">The message to process.</param>
    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        if (string.IsNullOrWhiteSpace(message.TargetEventId))
        {
            throw new KernelException("Internal Process Error: The target event id must be specified when sending a message to a step.").Log(this._logger);
        }

        string eventId = message.TargetEventId!;
        if (this._outputEdges!.TryGetValue(eventId, out List<KernelProcessEdge>? edges) && edges is not null)
        {
            foreach (var edge in edges)
            {
                // Create the external event that will be used to start the nested process. Since this event came
                // from outside this processes, we set the visibility to internal so that it's not emitted back out again.
                KernelProcessEvent nestedEvent = new() { Id = eventId, Data = message.TargetEventData };

                // Run the nested process completely within a single superstep.
                await this.RunOnceAsync(nestedEvent.ToJson()).ConfigureAwait(false);
            }
        }
    }

    internal static ActorId GetScopedGlobalErrorEventBufferId(string processId) => new($"{ProcessConstants.GlobalErrorEventId}_{processId}");

    #region Private Methods

    /// <summary>
    /// Initializes this process as a step within another process.
    /// </summary>
    protected override ValueTask ActivateStepAsync()
    {
        // The process does not need any further initialization as it's already been initialized.
        // Override the base method to prevent it from being called.
        return default;
    }

    private async Task InitializeProcessActorAsync(DaprProcessInfo processInfo, string? parentProcessId, string? eventProxyStepId)
    {
        Verify.NotNull(processInfo, nameof(processInfo));
        Verify.NotNull(processInfo.Steps);

        this.ParentProcessId = parentProcessId;
        this._process = processInfo;
        this._stepsInfos = [.. this._process.Steps];
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._process.State.Name) ?? new NullLogger<ProcessActor>();
        if (!string.IsNullOrWhiteSpace(eventProxyStepId))
        {
            this.EventProxyStepId = new ActorId(eventProxyStepId);
        }

        // Initialize the input and output edges for the process
        this._outputEdges = this._process.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());

        // Initialize the steps within this process
        foreach (var step in this._stepsInfos)
        {
            IStep? stepActor = null;

            // The current step should already have a name.
            Verify.NotNull(step.State?.Name);

            if (step is DaprProcessInfo processStep)
            {
                // The process will only have an Id if its already been executed.
                if (string.IsNullOrWhiteSpace(processStep.State.Id))
                {
                    processStep = processStep with { State = processStep.State with { Id = Guid.NewGuid().ToString() } };
                }

                // Initialize the step as a process.
                var scopedProcessId = this.ScopedActorId(new ActorId(processStep.State.Id!));
                var processActor = this.ProxyFactory.CreateActorProxy<IProcess>(scopedProcessId, nameof(ProcessActor));
                await processActor.InitializeProcessAsync(processStep, this.Id.GetId(), eventProxyStepId).ConfigureAwait(false);
                stepActor = this.ProxyFactory.CreateActorProxy<IStep>(scopedProcessId, nameof(ProcessActor));
            }
            else if (step is DaprMapInfo mapStep)
            {
                // Initialize the step as a map.
                ActorId scopedMapId = this.ScopedActorId(new ActorId(mapStep.State.Id!));
                IMap mapActor = this.ProxyFactory.CreateActorProxy<IMap>(scopedMapId, nameof(MapActor));
                await mapActor.InitializeMapAsync(mapStep, this.Id.GetId()).ConfigureAwait(false);
                stepActor = this.ProxyFactory.CreateActorProxy<IStep>(scopedMapId, nameof(MapActor));
            }
            else if (step is DaprProxyInfo proxyStep)
            {
                // Initialize the step as a proxy
                ActorId scopedProxyId = this.ScopedActorId(new ActorId(proxyStep.State.Id!));
                IProxy proxyActor = this.ProxyFactory.CreateActorProxy<IProxy>(scopedProxyId, nameof(ProxyActor));
                await proxyActor.InitializeProxyAsync(proxyStep, this.Id.GetId()).ConfigureAwait(false);
                stepActor = this.ProxyFactory.CreateActorProxy<IStep>(scopedProxyId, nameof(ProxyActor));
            }
            else
            {
                // The current step should already have an Id.
                Verify.NotNull(step.State?.Id);

                var scopedStepId = this.ScopedActorId(new ActorId(step.State.Id!));
                stepActor = this.ProxyFactory.CreateActorProxy<IStep>(scopedStepId, nameof(StepActor));
                await stepActor.InitializeStepAsync(step, this.Id.GetId(), eventProxyStepId).ConfigureAwait(false);
            }

            this._steps.Add(stepActor);
        }

        this._isInitialized = true;
    }

    private async Task Internal_ExecuteAsync(int maxSupersteps = 100, bool keepAlive = true, CancellationToken cancellationToken = default)
    {
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

                // Translate any global error events into an message that targets the appropriate step, when one exists.
                await this.HandleGlobalErrorMessageAsync().ConfigureAwait(false);

                // Check for external events
                await this.EnqueueExternalMessagesAsync().ConfigureAwait(false);

                // Reach out to all of the steps in the process and instruct them to retrieve their pending messages from their associated queues.
                var stepPreparationTasks = this._steps.Select(step => step.PrepareIncomingMessagesAsync()).ToArray();
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
                var stepProcessingTasks = this._steps.Select(step => step.ProcessIncomingMessagesAsync()).ToArray();
                await Task.WhenAll(stepProcessingTasks).ConfigureAwait(false);

                // Handle public events that need to be bubbled out of the process.
                await this.SendOutgoingPublicEventsAsync().ConfigureAwait(false);
            }
        }
        catch (Exception ex)
        {
            this._logger?.LogError(ex, "An error occurred while running the process: {ErrorMessage}.", ex.Message);
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
        IExternalEventBuffer externalEventQueue = this.ProxyFactory.CreateActorProxy<IExternalEventBuffer>(new ActorId(this.Id.GetId()), nameof(ExternalEventBufferActor));
        IList<string> dequeuedEvents = await externalEventQueue.DequeueAllAsync().ConfigureAwait(false);
        IList<KernelProcessEvent> externalEvents = dequeuedEvents.ToKernelProcessEvents();

        foreach (KernelProcessEvent externalEvent in externalEvents)
        {
            if (this._outputEdges!.TryGetValue(externalEvent.Id!, out List<KernelProcessEdge>? edges) && edges is not null)
            {
                foreach (KernelProcessEdge edge in edges)
                {
                    ProcessMessage message = ProcessMessageFactory.CreateFromEdge(edge, externalEvent.Id, externalEvent.Data);
                    var scopedMessageBufferId = this.ScopedActorId(new ActorId(edge.OutputTarget.StepId));
                    var messageQueue = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(scopedMessageBufferId, nameof(MessageBufferActor));
                    await messageQueue.EnqueueAsync(message.ToJson()).ConfigureAwait(false);
                }
            }
        }
    }

    /// <summary>
    /// Check for the presence of an global-error event and any edges defined for processing it.
    /// When both exist, the error event is processed and sent to the appropriate targets.
    /// </summary>
    private async Task HandleGlobalErrorMessageAsync()
    {
        var errorEventQueue = this.ProxyFactory.CreateActorProxy<IEventBuffer>(ProcessActor.GetScopedGlobalErrorEventBufferId(this.Id.GetId()), nameof(EventBufferActor));

        IList<string> errorEvents = await errorEventQueue.DequeueAllAsync().ConfigureAwait(false);
        if (errorEvents.Count == 0)
        {
            // No error events in queue.
            return;
        }

        var errorEdges = this.GetEdgeForEvent(ProcessConstants.GlobalErrorEventId).ToArray();
        if (errorEdges.Length == 0)
        {
            // No further action is required when there are no targetes defined for processing the error.
            return;
        }

        IList<ProcessEvent> processErrorEvents = errorEvents.ToProcessEvents();
        foreach (var errorEdge in errorEdges)
        {
            foreach (ProcessEvent errorEvent in processErrorEvents)
            {
                var errorMessage = ProcessMessageFactory.CreateFromEdge(errorEdge, errorEvent.SourceId, errorEvent.Data);
                var scopedErrorMessageBufferId = this.ScopedActorId(new ActorId(errorEdge.OutputTarget.StepId));
                var errorStepQueue = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(scopedErrorMessageBufferId, nameof(MessageBufferActor));
                await errorStepQueue.EnqueueAsync(errorMessage.ToJson()).ConfigureAwait(false);
            }
        }
    }

    /// <summary>
    /// Public events that are produced inside of this process need to be sent to the parent process. This method reads
    /// all of the public events from the event buffer and sends them to the targeted step in the parent process.
    /// </summary>
    private async Task SendOutgoingPublicEventsAsync()
    {
        // Loop through all steps that are processes and call a function requesting their outgoing events, then queue them up.
        if (!string.IsNullOrWhiteSpace(this.ParentProcessId))
        {
            // Handle public events that need to be bubbled out of the process.
            IEventBuffer eventQueue = this.ProxyFactory.CreateActorProxy<IEventBuffer>(new ActorId(this.Id.GetId()), nameof(EventBufferActor));
            IList<string> allEvents = await eventQueue.DequeueAllAsync().ConfigureAwait(false);
            IList<ProcessEvent> processEvents = allEvents.ToProcessEvents();

            foreach (ProcessEvent processEvent in processEvents)
            {
                ProcessEvent scopedEvent = this.ScopedEvent(processEvent);
                if (this._outputEdges!.TryGetValue(scopedEvent.QualifiedId, out List<KernelProcessEdge>? edges) && edges is not null)
                {
                    foreach (var edge in edges)
                    {
                        ProcessMessage message = ProcessMessageFactory.CreateFromEdge(edge, scopedEvent.SourceId, scopedEvent.Data);
                        var scopedMessageBufferId = this.ScopedActorId(new ActorId(edge.OutputTarget.StepId), scopeToParent: true);
                        var messageQueue = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(scopedMessageBufferId, nameof(MessageBufferActor));
                        await messageQueue.EnqueueAsync(message.ToJson()).ConfigureAwait(false);
                    }
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
        var scopedMessageBufferId = this.ScopedActorId(new ActorId(ProcessConstants.EndStepName));
        var endMessageQueue = this.ProxyFactory.CreateActorProxy<IMessageBuffer>(scopedMessageBufferId, nameof(MessageBufferActor));
        var messages = await endMessageQueue.DequeueAllAsync().ConfigureAwait(false);
        return messages.Count > 0;
    }

    /// <summary>
    /// Builds a <see cref="DaprProcessInfo"/> from the current <see cref="ProcessActor"/>.
    /// </summary>
    /// <returns>An instance of <see cref="DaprProcessInfo"/></returns>
    /// <exception cref="InvalidOperationException"></exception>
    private async Task<DaprProcessInfo> ToDaprProcessInfoAsync()
    {
        var processState = new KernelProcessState(this.Name, this._process!.State.Version, this.Id.GetId());
        var stepTasks = this._steps.Select(step => step.ToDaprStepInfoAsync()).ToList();
        var steps = await Task.WhenAll(stepTasks).ConfigureAwait(false);
        return new DaprProcessInfo { InnerStepDotnetType = this._process!.InnerStepDotnetType, Edges = this._process!.Edges, State = processState, Steps = [.. steps] };
    }

    /// <summary>
    /// Scopes the Id of a step within the process to the process.
    /// </summary>
    /// <param name="actorId">The actor Id to scope.</param>
    /// <param name="scopeToParent">Indicates if the Id should be scoped to the parent process.</param>
    /// <returns>A new <see cref="ActorId"/> which is scoped to the process.</returns>
    private ActorId ScopedActorId(ActorId actorId, bool scopeToParent = false)
    {
        if (scopeToParent && string.IsNullOrWhiteSpace(this.ParentProcessId))
        {
            throw new InvalidOperationException("The parent process Id must be set before scoping to the parent process.");
        }

        string id = scopeToParent ? this.ParentProcessId! : this.Id.GetId();
        return new ActorId($"{id}.{actorId.GetId()}");
    }

    /// <summary>
    /// Generates a scoped event for the step.
    /// </summary>
    /// <param name="daprEvent">The event.</param>
    /// <returns>A <see cref="ProcessEvent"/> with the correctly scoped namespace.</returns>
    private ProcessEvent ScopedEvent(ProcessEvent daprEvent)
    {
        Verify.NotNull(daprEvent);
        return daprEvent with { Namespace = $"{this.Name}_{this._process!.State.Id}" };
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
