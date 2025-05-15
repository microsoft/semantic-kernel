// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;
using Microsoft.SemanticKernel.Process.Serialization;

namespace Microsoft.SemanticKernel;

internal sealed class MapActor : StepActor, IMap
{
    private const string DaprProcessMapStateName = nameof(DaprMapInfo);

    private bool _isInitialized;
    private HashSet<string> _mapEvents = [];
    private ILogger? _logger;
    private KernelProcessMap? _map;

    internal DaprMapInfo? _mapInfo;

    /// <summary>
    /// Initializes a new instance of the <see cref="MapActor"/> class.
    /// </summary>
    /// <param name="host">The Dapr host actor</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    public MapActor(ActorHost host, Kernel kernel)
        : base(host, kernel)
    {
    }

    #region Public Actor Methods

    public async Task InitializeMapAsync(DaprMapInfo mapInfo, string? parentProcessId)
    {
        // Only initialize once. This check is required as the actor can be re-activated from persisted state and
        // this should not result in multiple initializations.
        if (this._isInitialized)
        {
            return;
        }

        this.InitializeMapActor(mapInfo, parentProcessId);

        this._isInitialized = true;

        // Save the state
        await this.StateManager.AddStateAsync(DaprProcessMapStateName, mapInfo).ConfigureAwait(false);
        await this.StateManager.AddStateAsync(ActorStateKeys.StepParentProcessId, parentProcessId).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// When the process is used as a step within another process, this method will be called
    /// rather than ToKernelProcessAsync when extracting the state.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public override Task<DaprStepInfo> ToDaprStepInfoAsync() => Task.FromResult<DaprStepInfo>(this._mapInfo!);

    protected override async Task OnActivateAsync()
    {
        var existingMapInfo = await this.StateManager.TryGetStateAsync<DaprMapInfo>(DaprProcessMapStateName).ConfigureAwait(false);
        if (existingMapInfo.HasValue)
        {
            this.ParentProcessId = await this.StateManager.GetStateAsync<string>(ActorStateKeys.StepParentProcessId).ConfigureAwait(false);
            this.InitializeMapActor(existingMapInfo.Value, this.ParentProcessId);
        }
    }

    /// <summary>
    /// The name of the step.
    /// </summary>
    protected override string Name => this._mapInfo?.State.Name ?? throw new KernelException("The Map must be initialized before accessing the Name property.");

    #endregion

    /// <summary>
    /// Handles a <see cref="ProcessMessage"/> that has been sent to the map.
    /// </summary>
    /// <param name="message">The message to map.</param>
    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        // Initialize the current operation
        (IEnumerable inputValues, KernelProcess mapOperation, string startEventId) = this._map!.Initialize(message, this._logger);

        List<Task> mapOperations = [];
        foreach (var value in inputValues)
        {
            KernelProcess mapProcess = mapOperation with { State = mapOperation.State with { Id = $"{this.Name}-{mapOperations.Count}-{Guid.NewGuid():N}" } };
            DaprKernelProcessContext processContext = new(mapProcess);
            Task processTask =
                processContext.StartWithEventAsync(
                    new KernelProcessEvent
                    {
                        Id = startEventId,
                        Data = value
                    },
                    eventProxyStepId: this.Id);

            mapOperations.Add(processTask);
        }

        // Wait for all the map operations to complete
        await Task.WhenAll(mapOperations).ConfigureAwait(false);

        // Retrieve all proxied events from the map operations
        IEventBuffer proxyBuffer = this.ProxyFactory.CreateActorProxy<IEventBuffer>(this.Id, nameof(EventBufferActor));
        IList<string> proxyEvents = await proxyBuffer.DequeueAllAsync().ConfigureAwait(false);
        IList<ProcessEvent> processEvents = proxyEvents.ToProcessEvents();

        // Survey the events to determine the type of the results associated with each event proxied by the map
        Dictionary<string, Type> capturedEvents = [];
        foreach (ProcessEvent processEvent in processEvents)
        {
            string eventName = processEvent.SourceId;
            if (this._mapEvents.Contains(eventName))
            {
                capturedEvents.TryGetValue(eventName, out Type? resultType);
                if (resultType is null || resultType == typeof(object))
                {
                    capturedEvents[eventName] = processEvent.Data?.GetType() ?? typeof(object);
                }
            }
        }

        // Correlate the operation results to emit as the map result
        Dictionary<string, Array> resultMap = [];
        Dictionary<string, int> resultCounts = [];

        foreach (ProcessEvent processEvent in processEvents)
        {
            string eventName = processEvent.SourceId;
            if (capturedEvents.TryGetValue(eventName, out Type? resultType))
            {
                var eventData = processEvent.Data;
                if (resultType == typeof(KernelProcessEventData) && eventData is KernelProcessEventData kernelProcessData)
                {
                    eventData = kernelProcessData.ToObject();
                    resultType = Type.GetType(kernelProcessData.ObjectType);
                }

                if (!resultMap.TryGetValue(eventName, out Array? results))
                {
                    results = Array.CreateInstance(resultType!, mapOperations.Count);
                    resultMap[eventName] = results;
                }

                resultCounts.TryGetValue(eventName, out int resultIndex); // resultIndex defaults to 0 when not found
                results.SetValue(eventData, resultIndex);
                resultCounts[eventName] = resultIndex + 1;
            }
        }

        // Emit map results
        foreach (string eventName in capturedEvents.Keys)
        {
            Array eventResult = resultMap[eventName];
            await this.EmitEventAsync(new KernelProcessEvent() { Id = eventName, Data = eventResult }).ConfigureAwait(false);
        }
    }

    private void InitializeMapActor(DaprMapInfo mapInfo, string? parentProcessId)
    {
        Verify.NotNull(mapInfo);
        Verify.NotNull(mapInfo.Operation);

        this._mapInfo = mapInfo;
        this._map = mapInfo.ToKernelProcessMap();
        this.ParentProcessId = parentProcessId;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._mapInfo.State.Name) ?? new NullLogger<MapActor>();
        this._outputEdges = this._mapInfo.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.ToList());
        this._eventNamespace = $"{this._mapInfo.State.Name}_{this._mapInfo.State.Id}";

        // Capture the events that the map is interested in as hashtable for performant lookup
        this._mapEvents = [.. this._mapInfo.Edges.Keys.Select(key => key.Split(ProcessConstants.EventIdSeparator).Last())];

        this._isInitialized = true;
    }

    private sealed record TypedResult(Type ResultType, Array Results);
}
