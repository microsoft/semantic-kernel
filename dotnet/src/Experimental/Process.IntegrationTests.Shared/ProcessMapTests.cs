// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using Xunit;
#pragma warning restore IDE0005 // Using directive is unnecessary.

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Integration test focusing on cycles in a process.
/// </summary>
[Collection(nameof(ProcessTestGroup))]
public class ProcessMapTests : IClassFixture<ProcessTestFixture>
{
    private readonly ProcessTestFixture _fixture;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessCycleTests"/> class. This is called by the test framework.
    /// </summary>
    /// <param name="fixture"></param>
    public ProcessMapTests(ProcessTestFixture fixture)
    {
        this._fixture = fixture;
    }

    /// <summary>
    /// Tests a process which cycles a fixed number of times and then exits.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task TestMapAsync()
    {
        // Arrange
        ProcessBuilder process = new(nameof(TestMapAsync));

        ProcessStepBuilder computeStep = process.AddStepFromType<ComputeStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(computeStep));
        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep);

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
        var processState = await processContext.GetStateAsync();
        var unionState = processState.Steps.Where(s => s.State.Name == "Union").FirstOrDefault()?.State as KernelProcessStepState<UnionState>;

        Assert.NotNull(unionState?.State);
        Assert.Equal(55L, unionState.State.SquareResult);
        Assert.Equal(225L, unionState.State.CubicResult);
    }
}
