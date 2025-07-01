// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;
using ProcessWithDapr.Processes;

namespace ProcessWithDapr.Controllers;

/// <summary>
/// A controller for chatbot.
/// </summary>
[ApiController]
public partial class ProcessController : ControllerBase
{
    private readonly DaprKernelProcessFactory _kernelProcessFactory;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessController"/> class.
    /// </summary>
    /// <param name="daprKernelProcessFactory">An instance of <see cref="DaprKernelProcessFactory"/></param>
    public ProcessController(DaprKernelProcessFactory daprKernelProcessFactory)
    {
        this._kernelProcessFactory = daprKernelProcessFactory ?? throw new ArgumentNullException(nameof(daprKernelProcessFactory));
    }

    /// <summary>
    /// Start and run a process.
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <returns></returns>
    [HttpGet("processes/{processId}")]
    public async Task<IActionResult> PostAsync(string processId)
    {
        var processContext = await this._kernelProcessFactory.StartAsync(ProcessWithCycle.Key, processId, new KernelProcessEvent() { Id = CommonEvents.StartProcess });
        return this.Ok(processId);
    }

    /// <summary>
    /// Common Events used in the process.
    /// </summary>
    private static class CommonEvents
    {
        public const string UserInputReceived = nameof(UserInputReceived);
        public const string CompletionResponseGenerated = nameof(CompletionResponseGenerated);
        public const string WelcomeDone = nameof(WelcomeDone);
        public const string AStepDone = nameof(AStepDone);
        public const string BStepDone = nameof(BStepDone);
        public const string CStepDone = nameof(CStepDone);
        public const string StartARequested = nameof(StartARequested);
        public const string StartBRequested = nameof(StartBRequested);
        public const string ExitRequested = nameof(ExitRequested);
        public const string StartProcess = nameof(StartProcess);
    }
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
}
