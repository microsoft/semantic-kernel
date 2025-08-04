// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.TestsShared.Services.Storage;
using Microsoft.SemanticKernel.Process.Tools;
using Step03.Processes;
using Utilities;

namespace Step03;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting different food related events.
/// For visual reference of the processes used here check the diagram in: https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step03a_foodPreparation
/// </summary>
public class Step03a_FoodPreparation(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    #region Stateless Processes
    [Fact]
    public async Task UsePrepareFriedFishProcessAsync()
    {
        var process = FriedFishProcess.CreateProcess();
        await UsePrepareSpecificProductAsync(process, FriedFishProcess.ProcessEvents.PrepareFriedFish);
    }

    [Fact]
    public async Task UsePreparePotatoFriesProcessAsync()
    {
        var process = PotatoFriesProcess.CreateProcess();
        await UsePrepareSpecificProductAsync(process, PotatoFriesProcess.ProcessEvents.PreparePotatoFries);
    }

    [Fact]
    public async Task UsePrepareFishSandwichProcessAsync()
    {
        var process = FishSandwichProcess.CreateProcess();

        string mermaidGraph = process.ToMermaid(1);
        Console.WriteLine($"=== Start - Mermaid Diagram for '{process.StepId}' ===");
        Console.WriteLine(mermaidGraph);
        Console.WriteLine($"=== End - Mermaid Diagram for '{process.StepId}' ===");

        await UsePrepareSpecificProductAsync(process, FishSandwichProcess.ProcessEvents.PrepareFishSandwich);
    }

    [Fact]
    public async Task UsePrepareFishAndChipsProcessAsync()
    {
        var process = FishAndChipsProcess.CreateProcess();
        await UsePrepareSpecificProductAsync(process, FishAndChipsProcess.ProcessEvents.PrepareFishAndChips);
    }
    #endregion
    #region Stateful Processes
    /// <summary>
    /// Test case that showcase when the same process is build multiple times, it will have different initial states
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task UsePrepareStatefulFriedFishProcessNoSharedStateAsync()
    {
        var processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV1();
        var externalTriggerEvent = FriedFishProcess.ProcessEvents.PrepareFriedFish;

        Kernel kernel = CreateKernelWithChatCompletion();

        // Assert
        Console.WriteLine($"=== Start SK Process '{processBuilder.StepId}' ===");
        await ExecuteProcessWithStateAsync(processBuilder.Build(), kernel, null, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(processBuilder.Build(), kernel, null, externalTriggerEvent, "Order 2");
        Console.WriteLine($"=== End SK Process '{processBuilder.StepId}' ===");
    }

    /// <summary>
    /// Test case that showcase when the same process is build once and used multiple times, it will have share the state
    /// and the state of the steps will become the initial state of the next running process
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task UsePrepareStatefulFriedFishProcessSharedStateAsync()
    {
        var processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV2();
        var externalTriggerEvent = FriedFishProcess.ProcessEvents.PrepareFriedFish;

        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = processBuilder.Build();

        Console.WriteLine($"=== Start SK Process '{processBuilder.StepId}' ===");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, null, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, null, externalTriggerEvent, "Order 2");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, null, externalTriggerEvent, "Order 3");
        Console.WriteLine($"=== End SK Process '{processBuilder.StepId}' ===");
    }

    [Fact]
    public async Task UsePrepareStatefulPotatoFriesProcessSharedStateAsync()
    {
        var processBuilder = PotatoFriesProcess.CreateProcessWithStatefulSteps();
        var externalTriggerEvent = PotatoFriesProcess.ProcessEvents.PreparePotatoFries;

        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = processBuilder.Build();

        Console.WriteLine($"=== Start SK Process '{processBuilder.StepId}' ===");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, null, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, null, externalTriggerEvent, "Order 2");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, null, externalTriggerEvent, "Order 3");
        Console.WriteLine($"=== End SK Process '{processBuilder.StepId}' ===");
    }

    private async Task<KernelProcess> ExecuteProcessWithStateAsync(KernelProcess process, Kernel kernel, IProcessStorageConnector? storageConnector, string externalTriggerEvent, string orderLabel = "Order 1", string? processId = null)
    {
        Console.WriteLine($"=== {orderLabel} ===");
        var runningProcess = await process.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = externalTriggerEvent,
            Data = new List<string>()
        }, processId, storageConnector: storageConnector);
        return await runningProcess.GetStateAsync();
    }

    #region Reading State from local file and apply to existing ProcessBuilder
    [Fact]
    public async Task RunStatefulFriedFishProcessFromFileAsync()
    {
        var processStatePath = GetSampleStep03DirPath(this._statefulFriedFishProcessFoldername);
        var stateFileStorage = new JsonFileStorage(processStatePath);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build();

        await ExecuteProcessWithStateAsync(processFromFile, kernel, stateFileStorage, FriedFishProcess.ProcessEvents.PrepareFriedFish, processId: this._processId);
    }

    [Fact]
    public async Task RunStatefulFriedFishProcessWithLowStockFromFileAsync()
    {
        var processStatePath = GetSampleStep03DirPath(this._statefulFriedFishLowStockProcessFoldername);
        var stateFileStorage = new JsonFileStorage(processStatePath);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build();

        await ExecuteProcessWithStateAsync(processFromFile, kernel, stateFileStorage, FriedFishProcess.ProcessEvents.PrepareFriedFish, processId: this._processId);
    }

    [Fact]
    public async Task RunStatefulFriedFishProcessWithNoStockFromFileAsync()
    {
        var processStatePath = GetSampleStep03DirPath(this._statefulFriedFishNoStockProcessFoldername);
        var stateFileStorage = new JsonFileStorage(processStatePath);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build();

        await ExecuteProcessWithStateAsync(processFromFile, kernel, stateFileStorage, FriedFishProcess.ProcessEvents.PrepareFriedFish, processId: this._processId);
    }

    [Fact]
    public async Task RunStatefulFishSandwichProcessFromFileAsync()
    {
        var processStatePath = GetSampleStep03DirPath(this._statefulFishSandwichProcessFoldername);
        var stateFileStorage = new JsonFileStorage(processStatePath);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FishSandwichProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build();

        await ExecuteProcessWithStateAsync(processFromFile, kernel, stateFileStorage, FishSandwichProcess.ProcessEvents.PrepareFishSandwich, processId: this._processId);
    }

    [Fact]
    public async Task RunStatefulFishSandwichProcessWithLowStockFromFileAsync()
    {
        var processStatePath = GetSampleStep03DirPath(this._statefulFishSandwichLowStockProcessFoldername);
        var stateFileStorage = new JsonFileStorage(processStatePath);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FishSandwichProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build();

        await ExecuteProcessWithStateAsync(processFromFile, kernel, stateFileStorage, FishSandwichProcess.ProcessEvents.PrepareFishSandwich, processId: this._processId);
    }

    #endregion
    #endregion
    protected async Task UsePrepareSpecificProductAsync(ProcessBuilder processBuilder, string externalTriggerEvent)
    {
        // Arrange
        Kernel kernel = CreateKernelWithChatCompletion();

        // Act
        KernelProcess kernelProcess = processBuilder.Build();

        // Assert
        Console.WriteLine($"=== Start SK Process '{processBuilder.StepId}' ===");
        await using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = externalTriggerEvent, Data = new List<string>()
        });
        Console.WriteLine($"=== End SK Process '{processBuilder.StepId}' ===");
    }

    // Step03a Utils for saving and loading SK Processes from/to repository
    private readonly string _processId = "myId";
    private readonly string _step03RelativePath = Path.Combine("Step03", "States");
    private readonly string _statefulFriedFishProcessFoldername = "FriedFishSuccess";
    private readonly string _statefulFriedFishLowStockProcessFoldername = "FriedFishSuccessLowStock";
    private readonly string _statefulFriedFishNoStockProcessFoldername = "FriedFishSuccessNoStock";
    private readonly string _statefulFishSandwichProcessFoldername = "FishSandwichSuccess";
    private readonly string _statefulFishSandwichLowStockProcessFoldername = "FishSandwichSuccessLowStock";

    private string GetSampleStep03DirPath(string dir)
    {
        var relativeDir = Path.Combine(this._step03RelativePath, dir);
        return FileStorageUtilities.GetRepositoryProcessStateFilepath(relativeDir, checkFilepathExists: true);
    }
}
