// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using Microsoft.Graph;
using ProcessWithCloudEvents.Processes;

namespace ProcessWithCloudEvents.Controllers;
[ApiController]
[Route("[controller]")]
public class CounterWithCloudStepsController : CounterBaseController
{
    private readonly ILogger<CounterWithCloudStepsController> _logger;

    public CounterWithCloudStepsController(ILogger<CounterWithCloudStepsController> logger, GraphServiceClient graphClient)
    {
        this._logger = logger;

        this.Kernel = this.BuildKernel(graphClient);
        this.Process = this.InitializeProcess(RequestCounterProcess.CreateProcessWithCloudSteps());
    }

    /// <inheritdoc/>
    [HttpGet("increase", Name = "IncreaseWithCloudSteps")]
    public override async Task<int> IncreaseCounterAsync()
    {
        var eventName = RequestCounterProcess.GetEventName(RequestCounterProcess.CounterProcessEvents.IncreaseCounterRequest);
        var runningProcess = await this.StartProcessWithEventAsync(eventName);
        var counterState = this.GetCounterState(runningProcess);

        return counterState?.State?.Counter ?? -1;
    }

    /// <inheritdoc/>
    [HttpGet("decrease", Name = "DecreaseWithCloudSteps")]
    public override async Task<int> DecreaseCounterAsync()
    {
        var eventName = RequestCounterProcess.GetEventName(RequestCounterProcess.CounterProcessEvents.DecreaseCounterRequest);
        var runningProcess = await this.StartProcessWithEventAsync(eventName);
        var counterState = this.GetCounterState(runningProcess);

        return counterState?.State?.Counter ?? -1;
    }

    /// <inheritdoc/>
    [HttpGet("reset", Name = "ResetCounterWithCloudSteps")]
    public override async Task<int> ResetCounterAsync()
    {
        var eventName = RequestCounterProcess.GetEventName(RequestCounterProcess.CounterProcessEvents.ResetCounterRequest);
        var runningProcess = await this.StartProcessWithEventAsync(eventName);
        var counterState = this.GetCounterState(runningProcess);

        return counterState?.State?.Counter ?? -1;
    }
}
