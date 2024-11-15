// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using Microsoft.Graph;
using ProcessWithCloudEvents.Processes;

namespace ProcessWithCloudEvents.Controllers;
[ApiController]
[Route("[controller]")]
public class CounterWithCloudSubscribersController : CounterBaseController
{
    private readonly ILogger<CounterWithCloudStepsController> _logger;

    public CounterWithCloudSubscribersController(ILogger<CounterWithCloudStepsController> logger, GraphServiceClient graphClient)
    {
        this._logger = logger;
        this.Kernel = this.BuildKernel();

        var serviceProvider = new ServiceCollection()
            .AddSingleton<GraphServiceClient>(graphClient)
            .BuildServiceProvider();
        this.Process = this.InitializeProcess(RequestCounterProcess.CreateProcessWithProcessSubscriber(serviceProvider));
    }

    [HttpGet("increase", Name = "IncreaseCounterWithCloudSubscribers")]
    public override async Task<int> IncreaseCounterAsync()
    {
        var eventName = RequestCounterProcess.GetEventName(RequestCounterProcess.CounterProcessEvents.IncreaseCounterRequest);
        var runningProcess = await this.StartProcessWithEventAsync(eventName);
        var counterState = this.GetCounterState(runningProcess);

        return counterState?.State?.Counter ?? -1;
    }

    [HttpGet("decrease", Name = "DecreaseCounterWithCloudSubscribers")]
    public override async Task<int> DecreaseCounterAsync()
    {
        var eventName = RequestCounterProcess.GetEventName(RequestCounterProcess.CounterProcessEvents.DecreaseCounterRequest);
        var runningProcess = await this.StartProcessWithEventAsync(eventName);
        var counterState = this.GetCounterState(runningProcess);

        return counterState?.State?.Counter ?? -1;
    }

    [HttpGet("reset", Name = "ResetCounterWithCloudSubscribers")]
    public async Task<int> ResetCounterAsync()
    {
        var eventName = RequestCounterProcess.GetEventName(RequestCounterProcess.CounterProcessEvents.ResetCounterRequest);
        var runningProcess = await this.StartProcessWithEventAsync(eventName);
        var counterState = this.GetCounterState(runningProcess);

        return counterState?.State?.Counter ?? -1;
    }
}
