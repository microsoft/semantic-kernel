// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Step04;

/// <summary>
/// %%% TBD
/// For visual reference of the processes used here check the diagram in: https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step04_mapreduce
/// </summary>
public class Step04a_MapReduce(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
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

    private static readonly long[] s_seedInput = [1, 2, 3, 4, 5];

    private async Task RunProcessAsync(string processName)
    {
        KernelProcess kernelProcess = SetupAgentProcess(processName);
        using LocalKernelProcessContext localProcess =
            await kernelProcess.StartAsync(
                new Kernel(),
                new KernelProcessEvent
                {
                    Id = "Map",
                    Data = s_seedInput
                });
    }

    private KernelProcess SetupAgentProcess(string processName)
    {
        ProcessBuilder process = new(processName);

        //var map = new MapStep<long>(ProcessFactory(), "Start", "Complete");
        var mapStep = process.AddStepFromType<MapStep1>();
        var unionStep = process.AddStepFromType<UnionStep>();
        var resultStep = process.AddStepFromType<ResultStep>();

        process
            .OnInputEvent("Map")
            .SendEventTo(new ProcessFunctionTargetBuilder(mapStep));

        mapStep
            .OnEvent("Complete")
            .SendEventTo(new ProcessFunctionTargetBuilder(unionStep));

        unionStep
            .OnEvent("Complete")
            .SendEventTo(new ProcessFunctionTargetBuilder(resultStep));

        KernelProcess kernelProcess = process.Build();

        return kernelProcess;
    }

    private static ProcessBuilder ProcessFactory()
    {
        ProcessBuilder process = new("Anything");

        var discreteStep = process.AddStepFromType<DiscreteStep>();

        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(discreteStep));

        return process;
    }

    private sealed class MapStep1 : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask MapAsync(KernelProcessStepContext context, long[] values, Kernel kernel)
        {
            System.Console.WriteLine($"MAP: {string.Join(", ", values)}");

            List<Task<LocalKernelProcessContext>> runningProcesses = [];
            foreach (long value in values)
            {
                var processBuilder = Step04a_MapReduce.ProcessFactory();

                ProcessBuilder mapBuilder = new("Map");
                var externalProcessStep = mapBuilder.AddStepFromProcess(processBuilder);
                var captureStep = mapBuilder.AddStepFromType<CaptureStep>();
                mapBuilder
                    .OnInputEvent("Start")
                    .SendEventTo(externalProcessStep);
                externalProcessStep
                    .OnEvent("Complete")
                    .SendEventTo(new ProcessFunctionTargetBuilder(captureStep));

                runningProcesses.Add(
                    mapBuilder.Build().StartAsync(
                        kernel,
                        new KernelProcessEvent
                        {
                            Id = "Start",
                            Data = value
                        }));
            }

            await Task.WhenAll(runningProcesses);

            long[] results = new long[runningProcesses.Count];
            for (int index = 0; index < runningProcesses.Count; ++index)
            {
                var processInfo = await runningProcesses[index].Result.GetStateAsync();
                results[index] =
                    processInfo.Steps
                        .Where(step => step.State.Name == nameof(CaptureStep))
                        .Select(step => step.State)
                        .OfType<KernelProcessStepState<CaptureState>>()
                        .Single()
                        .State!
                        .Value;
            }

            await context.EmitEventAsync(new() { Id = "Complete", Data = results });
        }

        private sealed record CaptureState
        {
            public long Value { get; set; }
        };

        private sealed class CaptureStep : KernelProcessStep<CaptureState>
        {
            private readonly CaptureState _capture = new();

            public override ValueTask ActivateAsync(KernelProcessStepState<CaptureState> state)
            {
                state.State = this._capture;
                return ValueTask.CompletedTask;
            }

            [KernelFunction]
            public void Compute(long value)
            {
                System.Console.WriteLine($"CAPTURE: {value}");
                this._capture!.Value = value;
            }
        }
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
