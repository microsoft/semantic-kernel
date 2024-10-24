// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using Dapr.Actors;
using Dapr.Actors.Runtime;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal sealed class MapActor : StepActor, IMap
{
    private const string DaprProcessMapStateName = nameof(DaprMapInfo);

    private bool _isInitialized;
    private ILogger? _logger;
    private IProcess? _mapOperation;

    internal DaprMapInfo? _map;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessActor"/> class.
    /// </summary>
    /// <param name="host">The Dapr host actor</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="loggerFactory">Optional. A <see cref="ILoggerFactory"/>.</param>
    public MapActor(ActorHost host, Kernel kernel, ILoggerFactory? loggerFactory)
        : base(host, kernel, loggerFactory)
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
        //await this.StateManager.AddStateAsync("parentProcessId", parentProcessId).ConfigureAwait(false);
        //await this.StateManager.AddStateAsync("kernelStepActivated", true).ConfigureAwait(false);
        await this.StateManager.SaveStateAsync().ConfigureAwait(false);
    }

    public async Task<DaprMapInfo> ToDaprMapInfoAsync()
    {
        KernelProcessMapState mapState = new(this.Name, this.Id.GetId());
        DaprProcessInfo mapOperation = await this._mapOperation!.GetProcessInfoAsync().ConfigureAwait(false);
        return new DaprMapInfo { InnerStepDotnetType = this._map!.InnerStepDotnetType, Edges = this._map!.Edges, State = mapState, MapStep = mapOperation };
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
            this.ParentProcessId = await this.StateManager.GetStateAsync<string>("parentProcessId").ConfigureAwait(false);
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
        await Task.Delay(0).ConfigureAwait(false); // %%% TODO
    }

    private async Task InitializeMapActorAsync(DaprMapInfo mapInfo, string? parentProcessId)
    {
        Verify.NotNull(mapInfo);
        Verify.NotNull(mapInfo.MapStep);

        this.ParentProcessId = parentProcessId;
        this._map = mapInfo;
        this._logger = this.LoggerFactory?.CreateLogger(this._map.State.Name) ?? new NullLogger<MapActor>();

        // Initialize the step as a process.
        DaprProcessInfo mapOperation = this._map.MapStep;
        ActorId processId = new(this._map.MapStep.State.Id!);
        this._mapOperation = this.ProxyFactory.CreateActorProxy<IProcess>(processId, nameof(ProcessActor));
        await this._mapOperation.InitializeProcessAsync(mapOperation, this.Id.GetId()).ConfigureAwait(false);

        this._isInitialized = true;
    }
}
