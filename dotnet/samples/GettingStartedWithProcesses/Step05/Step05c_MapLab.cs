// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using Microsoft.SemanticKernel;

namespace Step05;

/// <summary>
/// CONCEPTS
/// For visual reference of the processes used here check the diagram in: https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step04_mapreduce
/// </summary>
public class Step05c_MapLab(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    /// <summary>
    /// CONCEPTS
    /// </summary>
    [Fact]
    public void RunJoin()
    {
        long[] list = [1, 2, 3, 4, 5];

        Console.WriteLine(string.Join(",", (IEnumerable)list));
    }

    /// <summary>
    /// CONCEPTS
    /// </summary>
    [Fact]
    public async Task RunLabAsync()
    {
        await RunProcessAsync(SetupProcess<EnumerableObjectStep>(), (IEnumerable)s_seedInput);
        //await RunProcessAsync(SetupProcess<EnumerableTypeStep<long>>(), s_seedInput);
        await RunProcessAsync(SetupProcess<ArrayObjectStep>(), s_seedInput);
        await RunProcessAsync(SetupProcess<ArrayListObjectStep>(), new ArrayList(s_seedInput));
        await RunProcessAsync(SetupProcess<ListObjectStep>(), new ArrayList(s_seedInput));
        await RunProcessAsync(SetupProcess<ArrayTypeStep>(), s_seedInput);
        await RunProcessAsync(SetupProcess<ListTypeStep>(), new List<long>(s_seedInput));
    }

    private static readonly long[] s_seedInput = [11, 22, 33, 44, 55];

    private async Task RunProcessAsync(ProcessBuilder process, object input)
    {
        System.Console.WriteLine($"\nRUN: {process.Name}");

        using LocalKernelProcessContext localProcess =
            await process.Build().StartAsync(
                new Kernel(),
                new KernelProcessEvent
                {
                    Id = "Start",
                    Data = input
                });
    }

    private ProcessBuilder SetupProcess<TStep>() where TStep : KernelProcessStep
    {
        ProcessBuilder process = new(typeof(TStep).Name);

        var targetStep = process.AddStepFromType<TStep>();

        process
            .OnInputEvent("Start")
            .SendEventTo(new ProcessFunctionTargetBuilder(targetStep));

        return process;
    }

    private sealed class EnumerableObjectStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask LabAsync(IEnumerable values)
        {
            System.Console.WriteLine($"INPUT: {string.Join(",", values)}");
        }
    }

    private sealed class EnumerableTypeStep<TValue> : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask LabAsync(IEnumerable<TValue> values)
        {
            System.Console.WriteLine($"INPUT: {string.Join(",", values)}");
        }
    }

    private sealed class ArrayObjectStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask LabAsync(object[] values)
        {
            System.Console.WriteLine($"INPUT: {string.Join(",", values)}");
        }
    }

    private sealed class ArrayListObjectStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask LabAsync(ArrayList values)
        {
            System.Console.WriteLine($"INPUT: {string.Join(",", values)}");
        }
    }

    private sealed class ListObjectStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask LabAsync(List<object> values)
        {
            System.Console.WriteLine($"INPUT: {string.Join(",", values)}");
        }
    }

    private sealed class ArrayTypeStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask LabAsync(long[] values)
        {
            System.Console.WriteLine($"INPUT: {string.Join(",", values)}");
        }
    }

    private sealed class ListTypeStep : KernelProcessStep
    {
        [KernelFunction]
        public async ValueTask LabAsync(List<long> values)
        {
            System.Console.WriteLine($"INPUT: {string.Join(",", values)}");
        }
    }
}
;
