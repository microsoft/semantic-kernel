// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step05;

/// <summary>
/// %%% TBD
/// For visual reference of the processes used here check the diagram in: https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step04_mapreduce
/// </summary>
public class Step04b_MapReduce(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    [Fact]
    public async Task MathMapReduceAsync()
    {
        await RunProcessAsync(nameof(MathMapReduceAsync));
    }

    //private static readonly long[] s_seedInput = [11, 22, 33, 44, 55];
    private static readonly long[] s_seedInput = [123];

    private async Task RunProcessAsync(string processName)
    {
        KernelProcess kernelProcess = SetupAgentProcess(processName);
        using LocalKernelProcessContext localProcess =
            await kernelProcess.StartAsync(
                new Kernel(),
                new KernelProcessEvent
                {
                    Id = "Start",
                    Data = s_seedInput
                });
    }

    private KernelProcess SetupAgentProcess(string processName)
    {
        ProcessBuilder process = new(processName);

        var mapStep = process.AddMapFromType<DiscreteStep, long>("Start", "Complete");
        var unionStep = process.AddStepFromType<UnionStep>();
        var resultStep = process.AddStepFromType<ResultStep>();

        process
            .OnInputEvent("Start")
            .SendEventTo(mapStep.TargetFunction);

        mapStep
            .OnEvent("Complete")
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep));

        unionStep
            .OnEvent("Complete")
            .SendEventTo(new ProcessFunctionTargetBuilder(resultStep));

        KernelProcess kernelProcess = process.Build();

        return kernelProcess;
    }

    private sealed class DiscreteStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask ComputeAsync(KernelProcessStepContext context, long value)
        {
            System.Console.WriteLine($"DISCRETE: {value}");
            long square = value * value;
            await context.EmitEventAsync(new() { Id = "Complete", Data = square, Visibility = KernelProcessEventVisibility.Public });
        }
    }

    private sealed class UnionStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask ComputeAsync(KernelProcessStepContext context, long[] values)
        {
            System.Console.WriteLine($"UNION: {string.Join(", ", values)}");
            long sum = values.Sum();
            await context.EmitEventAsync(new() { Id = "Complete", Data = sum });
        }
    }

    private sealed class ResultStep : KernelProcessStep
    {
        [KernelFunction("Sum")]
        public async ValueTask ComputeAsync(KernelProcessStepContext context, long value)
        {
            System.Console.WriteLine($"RESULT: {value}");
        }
    }
}
;
