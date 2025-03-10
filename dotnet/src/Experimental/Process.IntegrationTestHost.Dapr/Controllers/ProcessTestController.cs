// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Dapr.Actors.Client;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Serialization;
using SemanticKernel.Process.TestsShared.CloudEvents;

namespace SemanticKernel.Process.IntegrationTests.Controllers;

/// <summary>
/// A controller for starting and managing processes.
/// </summary>
[ApiController]
[Route("/")]
[Produces("application/json")]
public class ProcessTestController : Controller
{
    private static readonly Dictionary<string, DaprKernelProcessContext> s_processes = new();
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessTestController"/> class.
    /// </summary>
    /// <param name="kernel"></param>
    public ProcessTestController(Kernel kernel)
    {
        this._kernel = kernel;
    }

    /// <summary>
    /// Starts a process.
    /// </summary>
    /// <param name="processId">The Id of the process</param>
    /// <param name="request">The request</param>
    /// <returns></returns>
    [HttpPost("processes/{processId}")]
    public async Task<IActionResult> StartProcessAsync(string processId, [FromBody] ProcessStartRequest request)
    {
        if (s_processes.ContainsKey(processId))
        {
            return this.BadRequest("Process already started");
        }

        KernelProcessEvent initialEvent = request.InitialEvent.ToKernelProcessEvent();

        var kernelProcess = request.Process.ToKernelProcess();
        var context = await kernelProcess.StartAsync(initialEvent);
        s_processes.Add(processId, context);

        return this.Ok();
    }

    /// <summary>
    /// Retrieves information about a process.
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <returns></returns>
    [HttpGet("processes/{processId}")]
    public async Task<IActionResult> GetProcessAsync(string processId)
    {
        if (!s_processes.TryGetValue(processId, out DaprKernelProcessContext? context))
        {
            return this.NotFound();
        }

        var process = await context.GetStateAsync();
        var daprProcess = DaprProcessInfo.FromKernelProcess(process);

        var serialized = JsonSerializer.Serialize(daprProcess);

        return this.Ok(daprProcess);
    }

    /// <summary>
    /// Retrieves current state of the MockCloudEventClient used in the running process
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <param name="cloudClient">Mock Cloud client ingested via dependency injection</param>
    /// <returns></returns>
    [HttpGet("processes/{processId}/mockCloudClient")]
    public Task<IActionResult> GetMockCloudClient(string processId, MockCloudEventClient cloudClient)
    {
        if (!s_processes.TryGetValue(processId, out DaprKernelProcessContext? context))
        {
            return Task.FromResult<IActionResult>(this.NotFound());
        }

        var cloudClientCopy = JsonSerializer.Deserialize<MockCloudEventClient>(JsonSerializer.Serialize<MockCloudEventClient>(cloudClient));
        cloudClient.Reset();

        return Task.FromResult<IActionResult>(this.Ok(cloudClientCopy));
    }

    /// <summary>
    /// Checks the health of the Dapr runtime by attempting to send a message to a health actor.
    /// </summary>
    /// <returns></returns>
    [HttpGet("daprHealth")]
    public async Task<IActionResult> HealthCheckAsync()
    {
        var healthActor = ActorProxy.Create<IHealthActor>(new Dapr.Actors.ActorId(Guid.NewGuid().ToString("n")), nameof(HealthActor));
        await healthActor.HealthCheckAsync();
        return this.Ok();
    }
}
