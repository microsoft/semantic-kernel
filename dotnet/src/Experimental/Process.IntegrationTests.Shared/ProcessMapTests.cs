// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Xunit;
#pragma warning restore IDE0005 // Using directive is unnecessary.

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Integration test focusing on <see cref="KernelProcessMap"/>.
/// </summary>
[Collection(nameof(ProcessTestGroup))]
public class ProcessMapTests : IClassFixture<ProcessTestFixture>
{
    private readonly ProcessTestFixture _fixture;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessMapTests"/> class. This is called by the test framework.
    /// </summary>
    public ProcessMapTests(ProcessTestFixture fixture)
    {
        this._fixture = fixture;
    }

    /// <summary>
    /// Tests a map-step with a step as the map-operation.
    /// </summary>
    [Fact]
    public async Task TestMapWithStepAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(TestMapWithStepAsync));

        ProcessMapBuilder mapStep = process.AddMapStepFromType<ComputeStep>();
        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));
        mapStep
            .OnEvent(ComputeStep.CubicEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumCubicFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        KernelProcessContext processContext =
            await this._fixture.StartProcessAsync(
                processInstance,
                kernel,
                new KernelProcessEvent()
                {
                    Id = "Start",
                    Data = new int[] { 1, 2, 3, 4, 5 }
                });

        // Assert
        KernelProcess processState = await processContext.GetStateAsync();
        KernelProcessStepState<UnionState> unionState = (KernelProcessStepState<UnionState>)processState.Steps.Where(s => s.State.StepId == "Union").Single().State;

        Assert.NotNull(unionState?.State);
        Assert.Equal(55L, unionState.State.SquareResult);
        Assert.Equal(225L, unionState.State.CubicResult);
    }

    /// <summary>
    /// Tests a map-step with a process as the map-operation.
    /// </summary>
    [Fact]
    public async Task TestMapWithProcessAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(TestMapWithStepAsync));

        ProcessBuilder mapProcess = new("MapOperation");
        ProcessStepBuilder computeStep = mapProcess.AddStepFromType<ComputeStep>();
        mapProcess
            .OnInputEvent("Anything")
            .SendEventTo(new ProcessFunctionTargetBuilder(computeStep));

        ProcessMapBuilder mapStep = process.AddMapStepFromProcess(mapProcess);
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep.WhereInputEventIs("Anything"));

        ProcessStepBuilder unionStep = process.AddStepFromType<UnionStep>("Union");
        mapStep
            .OnEvent(ComputeStep.SquareEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumSquareFunction));
        mapStep
            .OnEvent(ComputeStep.CubicEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep, UnionStep.SumCubicFunction));

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        KernelProcessContext processContext =
            await this._fixture.StartProcessAsync(
                processInstance with { State = processInstance.State with { RunId = Guid.NewGuid().ToString() } },
                kernel,
                new KernelProcessEvent()
                {
                    Id = "Start",
                    Data = new int[] { 1, 2, 3, 4, 5 }
                });

        // Assert
        KernelProcess processState = await processContext.GetStateAsync();
        KernelProcessStepState<UnionState> unionState = (KernelProcessStepState<UnionState>)processState.Steps.Where(s => s.State.StepId == "Union").Single().State;

        Assert.NotNull(unionState?.State);
        Assert.Equal(55L, unionState.State.SquareResult);
        Assert.Equal(225L, unionState.State.CubicResult);
    }
}
