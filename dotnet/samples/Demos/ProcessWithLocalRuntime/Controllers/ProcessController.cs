// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;

namespace ProcessWithDapr.Controllers;

/// <summary>
/// A controller for chatbot.
/// </summary>
[ApiController]
public class ProcessController : ControllerBase
{
    private readonly Kernel _kernel;
    private readonly IProcessStorageConnector _storageConnector;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessController"/> class.
    /// </summary>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="storageConnector">An implementation of instance of <see cref="IProcessStorageConnector"/> </param>
    public ProcessController(Kernel kernel, IProcessStorageConnector storageConnector)
    {
        this._kernel = kernel;
        this._storageConnector = storageConnector;
    }

    /// <summary>
    /// Start and run a process.
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <returns></returns>
    [HttpGet("processes/{processId}")]
    public async Task<IActionResult> PostAsync(string processId)
    {
        var process = this.GetProcess();
        var processContext = await process.StartAsync(this._kernel, new KernelProcessEvent() { Id = CommonEvents.StartProcess }, processId: processId, storageConnector: this._storageConnector);
        var finalState = await processContext.GetStateAsync();

        return this.Ok(processId);
    }

    private KernelProcess GetProcess()
    {
        // Create the process builder.
        ProcessBuilder processBuilder = new("ProcessWithDapr");

        // Add some steps to the process.
        var kickoffStep = processBuilder.AddStepFromType<KickoffStep>();
        var myAStep = processBuilder.AddStepFromType<AStep>();
        var myBStep = processBuilder.AddStepFromType<BStep>();

        // ########## Configuring initial state on steps in a process ###########
        // For demonstration purposes, we add the CStep and configure its initial state with a CurrentCycle of 1.
        // Initializing state in a step can be useful for when you need a step to start out with a predetermines
        // configuration that is not easily accomplished with dependency injection.
        var myCStep = processBuilder.AddStepFromType<CStep, CStepState>(initialState: new() { CurrentCycle = 1 });

        // Setup the input event that can trigger the process to run and specify which step and function it should be routed to.
        processBuilder
            .OnInputEvent(CommonEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        // When the kickoff step is finished, trigger both AStep and BStep.
        kickoffStep
            .OnEvent(CommonEvents.StartARequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myAStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(myBStep));

        // When step A and step B have finished, trigger the CStep.
        processBuilder
            .ListenFor()
                .AllOf(new()
                {
                    new(messageType: CommonEvents.AStepDone, source: myAStep),
                    new(messageType: CommonEvents.BStepDone, source: myBStep)
                })
                .SendEventTo(new ProcessStepTargetBuilder(myCStep, inputMapping: (inputEvents) =>
                {
                    // Map the input events to the CStep's input parameters.
                    // In this case, we are mapping the output of AStep to the first input parameter of CStep
                    // and the output of BStep to the second input parameter of CStep.
                    return new()
                    {
                        { "astepdata", inputEvents[$"{nameof(AStep)}.{CommonEvents.AStepDone}"] },
                        { "bstepdata", inputEvents[$"{nameof(BStep)}.{CommonEvents.BStepDone}"] }
                    };
                }));

        // When CStep has finished without requesting an exit, activate the Kickoff step to start again.
        myCStep
            .OnEvent(CommonEvents.CStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        // When the CStep has finished by requesting an exit, stop the process.
        myCStep
            .OnEvent(CommonEvents.ExitRequested)
            .StopProcess();

        var process = processBuilder.Build();
        return process;
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    // These classes are dynamically instantiated by the processes used in tests.

    /// <summary>
    /// Kick off step for the process.
    /// </summary>
    private sealed class KickoffStep : KernelProcessStep
    {
        public static class Functions
        {
            public const string KickOff = nameof(KickOff);
        }

        [KernelFunction(Functions.KickOff)]
        public async ValueTask PrintWelcomeMessageAsync(KernelProcessStepContext context)
        {
            Console.WriteLine("##### Kickoff ran.");
            await context.EmitEventAsync(new() { Id = CommonEvents.StartARequested, Data = "Get Going" });
        }
    }

    /// <summary>
    /// A step in the process.
    /// </summary>
    private sealed class AStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context)
        {
            Console.WriteLine("##### AStep ran.");
            await Task.Delay(TimeSpan.FromSeconds(1));
            await context.EmitEventAsync(CommonEvents.AStepDone, "I did A");
        }
    }

    /// <summary>
    /// A step in the process.
    /// </summary>
    private sealed class BStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context)
        {
            Console.WriteLine("##### BStep ran.");
            await Task.Delay(TimeSpan.FromSeconds(2));
            await context.EmitEventAsync(new() { Id = CommonEvents.BStepDone, Data = "I did B" });
        }
    }

    /// <summary>
    /// A stateful step in the process. This step uses <see cref="CStepState"/> as the persisted
    /// state object and overrides the ActivateAsync method to initialize the state when activated.
    /// </summary>
    private sealed class CStep : KernelProcessStep<CStepState>
    {
        private CStepState? _state;

        // ################ Using persisted state #################
        // CStep has state that we want to be persisted in the process. To ensure that the step always
        // starts with the previously persisted or configured state, we need to override the ActivateAsync
        // method and use the state object it provides.
        public override ValueTask ActivateAsync(KernelProcessStepState<CStepState> state)
        {
            this._state = state.State!;
            Console.WriteLine($"##### CStep activated with Cycle = '{state.State?.CurrentCycle}'.");
            return base.ActivateAsync(state);
        }

        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context, string astepdata, string bstepdata)
        {
            // ########### This method will restart the process in a loop until CurrentCycle >= 3 ###########
            this._state!.CurrentCycle++;
            if (this._state.CurrentCycle >= 3)
            {
                // Exit the processes
                Console.WriteLine("##### CStep run cycle 3 - exiting.");
                await context.EmitEventAsync(new() { Id = CommonEvents.ExitRequested });
                return;
            }

            // Cycle back to the start
            Console.WriteLine($"##### CStep run cycle {this._state.CurrentCycle}.");
            await context.EmitEventAsync(new() { Id = CommonEvents.CStepDone });
        }
    }

    /// <summary>
    /// A state object for the CStep.
    /// </summary>
    [DataContract]
    private sealed record CStepState
    {
        [DataMember]
        public int CurrentCycle { get; set; }
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
