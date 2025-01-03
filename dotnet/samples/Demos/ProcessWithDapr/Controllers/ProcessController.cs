// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;
using ProcessWithDapr.Processes;

namespace ProcessWithDapr.Controllers;

/// <summary>
/// A controller for chatbot.
/// </summary>
[ApiController]
public class ProcessController : ControllerBase
{
    private readonly Kernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessController"/> class.
    /// </summary>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    public ProcessController(Kernel kernel)
    {
        this._kernel = kernel;
    }

    /// <summary>
    /// Start and run a process.
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <returns></returns>
    [HttpGet("processes/{processId}")]
    public async Task<IActionResult> PostAsync(string processId)
    {
        var processContext = await ProcessManager.StartFormFillingProcessAsync(processId);
        //var processContext = await ProcessManager.StartProcessAsync(processId);
        var finalState = await processContext.GetStateAsync();

        return this.Ok(processId);
    }
}
