// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Dapr.Actors;
using Dapr.Actors.Runtime;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal sealed class MapActor : StepActor, IMap
{
    private const string DaprProcessMapStateName = nameof(DaprMapInfo);

    private bool _isInitialized;
    private HashSet<string> _mapEvents = [];
    private ILogger? _logger;
    private IProcess? _mapOperation; // %%% NEEDED ???

    internal DaprMapInfo? _map;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessActor"/> class.
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
        Verify.NotNull(mapInfo);
        Verify.NotNull(mapInfo.MapStep);

        // Only initialize once. This check is required as the actor can be re-activated from persisted state and
        // this should not result in multiple initializations.
        if (this._isInitialized)
        {
            return;
        }

        await this.InitializeMapActorAsync(mapInfo, parentProcessId).ConfigureAwait(false);

        this._isInitialized = true;

        // Save the state
        await this.StateManager.AddStateAsync(DaprProcessMapStateName, mapInfo).ConfigureAwait(false);
        await this.StateManager.AddStateAsync(ActorStateKeys.StepParentProcessId, parentProcessId).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    private async Task<DaprMapInfo> ToDaprMapInfoAsync() // %%% MOVE ???
    {
        DaprProcessInfo mapOperation = await this._mapOperation!.GetProcessInfoAsync().ConfigureAwait(false);
        return new DaprMapInfo { InnerStepDotnetType = this._map!.InnerStepDotnetType, Edges = this._map!.Edges, State = this._map.State, MapStep = mapOperation };
    }

    /// <summary>
    /// When the process is used as a step within another process, this method will be called
    /// rather than ToKernelProcessAsync when extracting the state.
    /// </summary>
    /// <returns>A <see cref="Task{T}"/> where T is <see cref="KernelProcess"/></returns>
    public override async Task<DaprStepInfo> ToDaprStepInfoAsync()
    {
        return await this.ToDaprMapInfoAsync().ConfigureAwait(false);
    }

    protected override async Task OnActivateAsync()
    {
        var existingMapInfo = await this.StateManager.TryGetStateAsync<DaprMapInfo>(DaprProcessMapStateName).ConfigureAwait(false);
        if (existingMapInfo.HasValue)
        {
            this.ParentProcessId = await this.StateManager.GetStateAsync<string>(ActorStateKeys.StepParentProcessId).ConfigureAwait(false);
            await this.InitializeMapActorAsync(existingMapInfo.Value, this.ParentProcessId).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// The name of the step.
    /// </summary>
    protected override string Name => this._map?.State.Name ?? throw new KernelException("The Map must be initialized before accessing the Name property.");

    #endregion

    /// <summary>
    /// Handles a <see cref="ProcessMessage"/> that has been sent to the map.
    /// </summary>
    /// <param name="message">The message to map.</param>
    internal override async Task HandleMessageAsync(ProcessMessage message)
    {
        IEnumerable values = message.GetMapInput(this.Logger);

        int index = 0;
        List<(Task Task, DaprKernelProcessContext ProcessContext, MapOperationContext Context)> mapOperations = [];
        Dictionary<string, Type> capturedEvents = [];

        KernelProcess process = this._map!.MapStep.ToKernelProcess().CloneProcess(this.Logger); // %%% EXTRA ???
        foreach (var value in values)
        {
            ++index;

            KernelProcess mapProcess = process with { State = process.State with { Id = $"{this.Name}-{index}-{Guid.NewGuid():N}" } };
            MapOperationContext context = new(index, this._mapEvents, capturedEvents);
            DaprKernelProcessContext processContext = new(mapProcess, this.Id); // %%% EVENT FILTER, context.Filter);
            Task processTask =
                processContext.StartWithEventAsync(
                    new KernelProcessEvent
                    {
                        Id = KernelProcessMap.MapEventId,
                        Data = value
                    });

            mapOperations.Add((processTask, processContext, context));
        }

        await Task.WhenAll(mapOperations.Select(p => p.Task)).ConfigureAwait(false);

        Dictionary<string, Array> resultMap = [];

        for (index = 0; index < mapOperations.Count; ++index)
        {
            foreach (var capturedEvent in capturedEvents)
            {
                string eventName = capturedEvent.Key;
                Type resultType = capturedEvent.Value;

                mapOperations[index].Context.Results.TryGetValue(eventName, out object? result);
                if (!resultMap.TryGetValue(eventName, out Array? results))
                {
                    results = Array.CreateInstance(resultType, mapOperations.Count);
                    resultMap[eventName] = results;
                }

                results.SetValue(result, index);
            }
        }

        foreach (var capturedEvent in capturedEvents)
        {
            string eventName = capturedEvent.Key;
            Array eventResult = resultMap[eventName];
            await this.EmitEventAsync(new KernelProcessEvent() { Id = eventName, Data = eventResult }).ConfigureAwait(false);
        }
    }

    private async Task InitializeMapActorAsync(DaprMapInfo mapInfo, string? parentProcessId)
    {
        Verify.NotNull(mapInfo);
        Verify.NotNull(mapInfo.MapStep);

        this.ParentProcessId = parentProcessId;
        this._map = mapInfo;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(this._map.State.Name) ?? new NullLogger<MapActor>();

        // Initialize the map operation as a process.
        DaprProcessInfo mapOperation = this._map.MapStep;
        ActorId processId = new(mapOperation.State.Id!);
        this._mapOperation = this.ProxyFactory.CreateActorProxy<IProcess>(processId, nameof(ProcessActor));
        await this._mapOperation.InitializeProcessAsync(mapOperation, this.ParentProcessId).ConfigureAwait(false);
        this._mapEvents = [.. this._map.Edges.Keys.Select(key => key.Split('.').Last())];

        this._isInitialized = true;
    }
}
