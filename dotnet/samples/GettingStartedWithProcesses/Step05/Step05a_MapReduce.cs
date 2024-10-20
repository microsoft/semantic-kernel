// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using Microsoft.SemanticKernel;

namespace Step05;

/// <summary>
/// POC
/// </summary>
public class Step05a_MapReduce(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    /// <summary>
    /// POC
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
        public async ValueTask MapAsync(KernelProcessStepContext context, IEnumerable values, Kernel kernel)
        {
            Type inputType = values.GetType();
            if (!inputType.HasElementType)
            {
                throw new KernelException("%%%"); // MESSAGE
            }
            Type elementType = inputType.GetElementType()!;
            List<object> valueList = [.. values];
            System.Console.WriteLine($"MAP: {string.Join(", ", valueList)} [{elementType.Name}]");

            List<Task<LocalKernelProcessContext>> runningProcesses = [];
            foreach (long value in values)
            {
                var processBuilder = Step05a_MapReduce.ProcessFactory();

                ProcessBuilder mapBuilder = new("Map");
                var externalProcessStep = mapBuilder.AddStepFromProcess(processBuilder);
                var captureStep = mapBuilder.AddStepFromType<CaptureStep>();
                mapBuilder
                    .OnInputEvent("Start")
                    .SendEventTo(externalProcessStep.WhereInputEventIs("Start"));

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

            Array results = Array.CreateInstance(elementType, runningProcesses.Count);
            //Type listType = typeof(List<>);
            //Type[] typeArgs = { elementType };
            //Type genericListType = listType.MakeGenericType(typeArgs);
            //IList results = (IList)(Activator.CreateInstance(genericListType) ?? throw new InvalidOperationException("Failed!!!"));

            for (int index = 0; index < runningProcesses.Count; ++index)
            {
                var processInfo = await runningProcesses[index].Result.GetStateAsync();
                var result =
                    processInfo.Steps
                        .Where(step => step.State.Name == nameof(CaptureStep))
                        .Select(step => step.State)
                        .OfType<KernelProcessStepState<CaptureState>>()
                        .Single()
                        .State!
                        .Value;
                results.SetValue(result, index);
                //results.Add(result);
            }

            await context.EmitEventAsync(new() { Id = "Complete", Data = results });
        }

        private sealed record CaptureState
        {
            public object Value { get; set; }
        };

        private sealed class CaptureStep : KernelProcessStep<CaptureState>
        {
            private CaptureState? _capture;

            public override ValueTask ActivateAsync(KernelProcessStepState<CaptureState> state)
            {
                this._capture = state.State;
                return ValueTask.CompletedTask;
            }

            [KernelFunction]
            public void Compute(object value)
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
        // NO: Forces one or the other
        //public async ValueTask ComputeAsync(KernelProcessStepContext context, long[] values)
        //public async ValueTask ComputeAsync(KernelProcessStepContext context, List<long> values)

        // Yes: Allows either.
        //public async ValueTask ComputeAsync(KernelProcessStepContext context, IList<long> values)
        public async ValueTask ComputeAsync(KernelProcessStepContext context, IEnumerable<long> values)
        //public async ValueTask ComputeAsync(KernelProcessStepContext context, IReadOnlyList<long> values)
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
