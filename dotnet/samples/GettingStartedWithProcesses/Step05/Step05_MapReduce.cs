// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using Microsoft.SemanticKernel;

namespace Step05;

/// <summary>
/// DEV HARNESS
/// </summary>
public class Step05_MapReduce : BaseTest
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    /// <summary>
    /// Factor to increase the scale of the content processed to highlight the characteristics of
    /// each approach: map vs linear.
    /// </summary>
    private const int ScaleFactor = 100;

    private readonly string _sourceContent;

    public Step05_MapReduce(ITestOutputHelper output)
         : base(output, redirectSystemConsoleOutput: true)
    {
        StringBuilder content = new();

        for (int count = 0; count < ScaleFactor; ++count)
        {
            content.AppendLine(File.ReadAllText("Grimms-The-King-of-the-Golden-Mountain.txt"));
            content.AppendLine(File.ReadAllText("Grimms-The-Water-of-Life.txt"));
            content.AppendLine(File.ReadAllText("Grimms-The-White-Snake.txt"));
        }

        this._sourceContent = content.ToString().ToUpperInvariant();
    }

    [Fact]
    public async Task RunMapReduceAsync()
    {
        KernelProcess process = SetupMapReduceProcess(nameof(RunMapReduceAsync), "Start");
        Kernel kernel = new();
        using LocalKernelProcessContext localProcess =
            await process.StartAsync(
                kernel,
                new KernelProcessEvent
                {
                    Id = "Start",
                    Data = this._sourceContent,
                });

        Dictionary<string, int> results = (Dictionary<string, int>?)kernel.Data[ResultStep.ResultKey] ?? [];
        foreach (var result in results)
        {
            Console.WriteLine($"{result.Key}: {result.Value}");
        }
    }

    [Fact]
    public async Task RunLinearAsync()
    {
        Dictionary<string, int> counts = [];

        string[] words = this._sourceContent.Split([' ', '\n', '\r', '.', ',', '’'], StringSplitOptions.RemoveEmptyEntries);
        foreach (string word in words)
        {
            if (s_notInteresting.Contains(word))
            {
                continue;
            }

            counts.TryGetValue(word.Trim(), out int count);
            counts[word] = ++count;
        }

        var sorted =
            from kvp in counts
            orderby kvp.Value descending
            select kvp;

        foreach (var result in sorted.Take(10))
        {
            Console.WriteLine($"{result.Key}: {result.Value}");
        }
    }

    private KernelProcess SetupMapReduceProcess(string processName, string inputEventId)
    {
        ProcessBuilder process = new(processName);

        ProcessStepBuilder chunkStep = process.AddStepFromType<ChunkStep>();
        process
            .OnInputEvent(inputEventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(chunkStep));

        ProcessStepBuilder countStep = process.AddStepFromType<CountStep>();
        ProcessMapBuilder mapStep = process.AddMapForTarget(new ProcessFunctionTargetBuilder(countStep));
        chunkStep
            .OnEvent(ChunkStep.EventId)
            .SendEventTo(mapStep);

        ProcessStepBuilder resultStep = process.AddStepFromType<ResultStep>();
        mapStep
            .OnEvent(CountStep.EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(resultStep));

        return process.Build();
    }

    private sealed class ChunkStep : KernelProcessStep
    {
        public const string EventId = "ChunkComplete";

        [KernelFunction]
        public async ValueTask ChunkAsync(KernelProcessStepContext context, string content)
        {
            int chunkSize = content.Length / Environment.ProcessorCount;
            string[] chunks = ChunkContent(content, chunkSize).ToArray();

            await context.EmitEventAsync(new() { Id = EventId, Data = chunks });
        }

        private IEnumerable<string> ChunkContent(string content, int chunkSize)
        {
            for (int index = 0; index < content.Length; index += chunkSize)
            {
                yield return content.Substring(index, Math.Min(chunkSize, content.Length - index));
            }
        }
    }

    private sealed class CountStep : KernelProcessStep
    {
        public const string EventId = "CountComplete";

        [KernelFunction]
        public async ValueTask ComputeAsync(KernelProcessStepContext context, string chunk)
        {
            Dictionary<string, int> counts = [];

            string[] words = chunk.Split([' ', '\n', '\r', '.', ',', '’'], StringSplitOptions.RemoveEmptyEntries);
            foreach (string word in words)
            {
                if (s_notInteresting.Contains(word))
                {
                    continue;
                }

                counts.TryGetValue(word.Trim(), out int count);
                counts[word] = ++count;
            }

            await context.EmitEventAsync(new() { Id = EventId, Data = counts });
        }
    }

    private sealed class ResultStep : KernelProcessStep
    {
        public const string ResultKey = "WordCount";

        [KernelFunction]
        public async ValueTask ComputeAsync(KernelProcessStepContext context, IList<Dictionary<string, int>> results, Kernel kernel)
        {
            Dictionary<string, int> totals = [];

            foreach (Dictionary<string, int> result in results)
            {
                foreach (KeyValuePair<string, int> pair in result)
                {
                    totals.TryGetValue(pair.Key, out int count);
                    totals[pair.Key] = count + pair.Value;
                }
            }

            var sorted =
                from kvp in totals
                orderby kvp.Value descending
                select kvp;

            kernel.Data[ResultKey] = sorted.Take(10).ToDictionary(kvp => kvp.Key, kvp => kvp.Value);
        }
    }

    private static readonly HashSet<string> s_notInteresting =
        [
            "A",
            "ALL",
            "AN",
            "AND",
            "AS",
            "AT",
            "BE",
            "BEFORE",
            "BUT",
            "BY",
            "CAME",
            "COULD",
            "FOR",
            "GO",
            "HAD",
            "HAVE",
            "HE",
            "HER",
            "HIM",
            "HIMSELF",
            "HIS",
            "HOW",
            "I",
            "IF",
            "IN",
            "INTO",
            "IS",
            "IT",
            "ME",
            "MUST",
            "MY",
            "NO",
            "NOT",
            "NOW",
            "OF",
            "ON",
            "ONCE",
            "ONE",
            "ONLY",
            "OUT",
            "S",
            "SAID",
            "SAW",
            "SET",
            "SHE",
            "SHOULD",
            "SO",
            "THAT",
            "THE",
            "THEM",
            "THEN",
            "THEIR",
            "THERE",
            "THEY",
            "THIS",
            "TO",
            "VERY",
            "WAS",
            "WENT",
            "WERE",
            "WHAT",
            "WHEN",
            "WHO",
            "WILL",
            "WITH",
            "WOULD",
            "UP",
            "UPON",
            "YOU",
        ];
}
