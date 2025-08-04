// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;
#pragma warning restore IDE0005 // Using directive is unnecessary.

namespace Microsoft.SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Integration test focusing on cycles in a process.
/// </summary>
[Collection(nameof(ProcessTestGroup))]
public class ProcessCycleTests : IClassFixture<ProcessTestFixture>
{
    private readonly ProcessTestFixture _fixture;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessCycleTests"/> class. This is called by the test framework.
    /// </summary>
    /// <param name="fixture"></param>
    public ProcessCycleTests(ProcessTestFixture fixture)
    {
        this._fixture = fixture;
    }

    /// <summary>
    /// Tests a process which cycles a fixed number of times and then exits.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task TestCycleAndExitWithFanInAsync()
    {
        Kernel kernel = new();

        ProcessBuilder process = new("Test Process");

        var kickoffStep = process.AddStepFromType<KickoffStep>();
        var myAStep = process.AddStepFromType<AStep>();
        var myBStep = process.AddStepFromType<BStep>();
        var myCStep = process.AddStepFromType<CStep>();

        process
            .OnInputEvent(CommonEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        kickoffStep
            .OnEvent(CommonEvents.StartARequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myAStep));

        kickoffStep
            .OnEvent(CommonEvents.StartBRequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myBStep));

        process.ListenFor().AllOf(
            [
                new(CommonEvents.AStepDone, myAStep),
                new(CommonEvents.BStepDone, myBStep)
            ])
            .SendEventTo(new ProcessStepTargetBuilder(myCStep, inputMapping: (inputEvents) =>
            {
                return new()
                {
                    { "astepdata", inputEvents[myAStep.GetFullEventId(CommonEvents.AStepDone)] },
                    { "bstepdata", inputEvents[myBStep.GetFullEventId(CommonEvents.BStepDone)] }
                };
            }));

        myCStep
            .OnEvent(CommonEvents.CStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        myCStep
            .OnEvent(CommonEvents.ExitRequested)
            .StopProcess();

        KernelProcess kernelProcess = process.Build();
        var processContext = await this._fixture.StartProcessAsync(kernelProcess, kernel, new KernelProcessEvent() { Id = CommonEvents.StartProcess, Data = "foo" });

        var processState = await processContext.GetStateAsync();
        var cStepState = processState.Steps.Where(s => s.State.StepId == "CStep").FirstOrDefault()?.State as KernelProcessStepState<CStepState>;

        Assert.NotNull(cStepState?.State);
        Assert.Equal(3, cStepState.State.CurrentCycle);
    }
}
