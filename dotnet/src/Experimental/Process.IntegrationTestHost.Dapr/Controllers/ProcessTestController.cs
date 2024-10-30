// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Dapr.Actors.Client;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;

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
    [HttpPost("processes/{processId}/start")]
    public async Task<IActionResult> StartProcessAsync(string processId, [FromBody] ProcessStartRequest request)
    {
        try
        {
            if (s_processes.ContainsKey(processId))
            {
                return this.BadRequest("Process already started");
            }

            if (request.InitialEvent?.Data is JsonElement jsonElement)
            {
                object? data = jsonElement.Deserialize<string>();
                request.InitialEvent = request.InitialEvent with { Data = data };
            }

            var kernelProcess = request.Process.ToKernelProcess();
            var context = await kernelProcess.StartAsync(this._kernel, request.InitialEvent!);
            s_processes.Add(processId, context);

            return this.Ok();
        }
        catch (Exception ex)
        {
            throw;
        }
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
    /// Checks the health of the Dapr runtime.
    /// </summary>
    /// <returns></returns>
    [HttpGet("daprHealth")]
    public async Task<IActionResult> HealthCheckAsync()
    {
        try
        {
            var healthActor = ActorProxy.Create<IHealthActor>(new Dapr.Actors.ActorId(Guid.NewGuid().ToString("n")), nameof(HealthActor));
            await healthActor.HealthCheckAsync();
            return this.Ok();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"####### Health check failed with exception of type '{ex.GetType().Name}'.");
            return this.NotFound();
        }
    }
}
