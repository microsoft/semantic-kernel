// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using Google.Protobuf.WellKnownTypes;
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
        var process = this.GetProcess();
        var processContext = await process.Build().StartAsync(new KernelProcessEvent() { Id = CommonEvents.StartProcess, Data = 3 }, processId);
        var finalState = await processContext.GetStateAsync();

        return this.Ok(processId);
    }

    /// <summary>
    /// Start and run a process.
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <returns></returns>
    [HttpGet("sub/{processId}")]
    public async Task<IActionResult> SubAsync(string processId)
    {
        var subProcess = this.GetProcess();
        ProcessBuilder process = new("Another");
        process.AddStepFromProcess(subProcess);
        process.OnInputEvent("CommonEvents.StartProcess").SendEventTo(subProcess.WhereInputEventIs(CommonEvents.StartProcess));
        var processContext = await process.Build().StartAsync(new KernelProcessEvent() { Id = CommonEvents.StartProcess, Data = 3 }, processId);
        var finalState = await processContext.GetStateAsync();

        return this.Ok(processId);
    }

    /// <summary>
    /// Start and run a map operation.
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <returns></returns>
    [HttpGet("maps/{processId}")]
    public async Task<IActionResult> MapAsync(string processId)
    {
        Console.WriteLine("##### Map Controller.");

        var process = this.GetMapProcess(CommonEvents.StartProcess);
        //List<int> inputParams = [1, 2, 3, 4, 5];
        int[] inputParams = [1, 2, 3, 4, 5];
        //MapParameters inputParams = [1, 2, 3, 4, 5];
        var processContext = await process.Build().StartAsync(new KernelProcessEvent() { Id = CommonEvents.StartProcess, Data = inputParams }, processId);
        //var processContext = await process.Build().StartAsync(this._kernel, new KernelProcessEvent() { Id = CommonEvents.StartProcess }, processId: processId);
        var finalState = await processContext.GetStateAsync();

        return this.Ok(processId);
    }

    private ProcessBuilder GetMapProcess(string initialEventId)
    {
        ProcessBuilder process = new("MapProcess");

        ProcessStepBuilder initStep = process.AddStepFromType<SeedStep>();

        ProcessStepBuilder computeStep = process.AddStepFromType<ComputeStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep));
        process
            .OnInputEvent(initialEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(initStep));

        initStep
            .OnEvent(SeedStep.EventId)
            .SendEventTo(mapStep);

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>();
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumFunction));

        return process;
    }

    /// <summary>
    /// Start and run a map operation.
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <returns></returns>
    [HttpGet("inputone/{processId}")]
    public async Task<IActionResult> Input1Async(string processId)
    {
        Console.WriteLine("##### Input Controller.");

        var process = this.GetInput1Process(CommonEvents.StartProcess);
        var processContext = await process.Build().StartAsync(new KernelProcessEvent() { Id = CommonEvents.StartProcess, Data = "hello" }, processId);
        var finalState = await processContext.GetStateAsync();

        return this.Ok(processId);
    }

    /// <summary>
    /// Start and run a map operation.
    /// </summary>
    /// <param name="processId">The Id of the process.</param>
    /// <returns></returns>
    [HttpGet("inputtwo/{processId}")]
    public async Task<IActionResult> Input2Async(string processId)
    {
        Console.WriteLine("##### Input Controller.");

        var input = new DStepInput { Value = "hello" };
        var process = this.GetInput2Process(CommonEvents.StartProcess);
        var processContext = await process.Build().StartAsync(new KernelProcessEvent() { Id = CommonEvents.StartProcess, Data = input }, processId);
        var finalState = await processContext.GetStateAsync();

        return this.Ok(processId);
    }

    private ProcessBuilder GetInput1Process(string initialEventId)
    {
        ProcessBuilder process = new("SimpleInput");

        ProcessStepBuilder initStep = process.AddStepFromType<DStep>();
        process
            .OnInputEvent(initialEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(initStep, DStep.SimpleFunction, "input"));

        return process;
    }

    private ProcessBuilder GetInput2Process(string initialEventId)
    {
        ProcessBuilder process = new("ComplexInput");

        ProcessStepBuilder initStep = process.AddStepFromType<DStep>();
        process
            .OnInputEvent(initialEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(initStep, DStep.ComplexFunction, "input"));

        return process;
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    // These classes are dynamically instantiated by the processes used in tests.

    [KnownType(typeof(int[]))]
    //[KnownType(typeof(MapParameters))]
    private sealed class MapParameters : List<int>
    {
    }

    /// <summary>
    /// Kick off step for the process.
    /// </summary>
    private sealed class SeedStep : KernelProcessStep
    {
        public const string EventId = "Init";

        [KernelFunction]
        public async ValueTask SeedMapAsync(KernelProcessStepContext context, int[] values)
        {
            Console.WriteLine("##### Seed Map: " + values.Length);
            await context.EmitEventAsync(new() { Id = "Init", Data = values });
            Console.WriteLine("##### Seed Done");
        }
    }
    /// <summary>
    /// A step that contains a map operation that emits two events.
    /// </summary>
    private sealed class ComputeStep : KernelProcessStep
    {
        public const string SquareEventId = "SquareResult";
        public const string ComputeFunction = "MapCompute";

        [KernelFunction(ComputeFunction)]
        public async ValueTask ComputeAsync(KernelProcessStepContext context, long value)
        {
            Console.WriteLine("##### Compute Ran.");
            long square = value * value;
            await context.EmitEventAsync(new() { Id = SquareEventId, Data = square });
        }
    }

    /// <summary>
    /// The step that combines the results of the map operation.
    /// </summary>
    private sealed class UnionStep : KernelProcessStep
    {
        public const string ResultKey = "Result";
        public const string EventId = "MapUnion";
        public const string SumFunction = "UnionSum";

        [KernelFunction(SumFunction)]
        public async ValueTask SumAsync(KernelProcessStepContext context, IList<long> values, Kernel kernel)
        {
            long sum = values.Sum();
            Console.WriteLine($"##### Union Ran: {sum}");
            kernel.Data[ResultKey] = sum;
            await context.EmitEventAsync(new() { Id = EventId, Data = sum });
        }
    }

    private ProcessBuilder GetProcess()
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
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep, parameterName: "value"));

        // When the kickoff step is finished, trigger both AStep and BStep.
        kickoffStep
            .OnEvent(CommonEvents.StartARequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myAStep, parameterName: "message"))
            .SendEventTo(new ProcessFunctionTargetBuilder(myBStep, parameterName: "message"));

        // When AStep finishes, send its output to CStep.
        myAStep
            .OnEvent(CommonEvents.AStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(myCStep, parameterName: "astepdata"));

        // When BStep finishes, send its output to CStep also.
        myBStep
            .OnEvent(CommonEvents.BStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(myCStep, parameterName: "bstepdata"));

        // When CStep has finished without requesting an exit, activate the Kickoff step to start again.
        myCStep
            .OnEvent(CommonEvents.CStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        // When the CStep has finished by requesting an exit, stop the process.
        myCStep
            .OnEvent(CommonEvents.ExitRequested)
            .StopProcess();

        return processBuilder;
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
        public async ValueTask PrintWelcomeMessageAsync(KernelProcessStepContext context, int value)
        {
            //Console.WriteLine("##### Kickoff ran");
            Console.WriteLine("##### Kickoff ran: " + value);
            await context.EmitEventAsync(new() { Id = CommonEvents.StartARequested, Data = "Get Going" });
        }
    }

    /// <summary>
    /// A step in the process.
    /// </summary>
    private sealed class AStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context, string message)
        {
            Console.WriteLine("##### AStep ran: " + message);
            await Task.Delay(TimeSpan.FromSeconds(1));
            await context.EmitEventAsync(new() { Id = CommonEvents.AStepDone, Data = "I did A" });
        }
    }

    /// <summary>
    /// A step in the process.
    /// </summary>
    private sealed class BStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask DoItAsync(KernelProcessStepContext context, string message)
        {
            Console.WriteLine("##### BStep ran: " + message);
            await Task.Delay(TimeSpan.FromSeconds(2));
            await context.EmitEventAsync(new() { Id = CommonEvents.BStepDone, Data = "I did B" });
        }
    }

    /// <summary>
    /// A stateful step in the process. This step uses <see cref="CStepState"/> as the persisted
    /// state object and overrides the ActivateAsync method to initialize the state when activated.
    /// </summary>
    [KnownType(typeof(CStepState))]
    [KnownType(typeof(KernelProcessStepState<CStepState>))]
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
        public async ValueTask ReportAsync(KernelProcessStepContext context, string astepdata, string bstepdata)
        {
            Console.WriteLine($"##### CStep run cycle {this._state?.CurrentCycle ?? 0} - invoke: {astepdata}/{bstepdata}");

            // ########### This method will restart the process in a loop until CurrentCycle >= 3 ###########
            this._state!.CurrentCycle++;

            if (this._state.CurrentCycle >= 3)
            {
                // Exit the processes
                Console.WriteLine($"##### CStep run cycle {this._state.CurrentCycle} - exiting.");
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
    [KnownType(typeof(KernelProcessStepState<CStepState>))]
    private sealed record CStepState
    {
        [DataMember]
        public int CurrentCycle { get; set; }
    }

    private sealed class DStep : KernelProcessStep
    {
        public const string ComplexFunction = "Complex";
        public const string SimpleFunction = "Simple";

        [KernelFunction(ComplexFunction)]
        public async ValueTask ComplexAsync(KernelProcessStepContext context, DStepInput input)
        {
            Console.WriteLine("##### DSTEP: " + input.Value);
        }

        [KernelFunction(SimpleFunction)]
        public async ValueTask SimpleAsync(KernelProcessStepContext context, string input)
        {
            Console.WriteLine("##### DSTEP: " + input);
        }
    }

    [DataContract]
    private sealed record DStepInput
    {
        [DataMember]
        public string Value { get; set; } = string.Empty;
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
