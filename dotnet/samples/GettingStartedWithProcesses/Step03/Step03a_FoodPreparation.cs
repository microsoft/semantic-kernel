// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Models;
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
        Console.WriteLine($"=== Start - Mermaid Diagram for '{process.Name}' ===");
        Console.WriteLine(mermaidGraph);
        Console.WriteLine($"=== End - Mermaid Diagram for '{process.Name}' ===");

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
        Console.WriteLine($"=== Start SK Process '{processBuilder.Name}' ===");
        await ExecuteProcessWithStateAsync(processBuilder.Build(), kernel, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(processBuilder.Build(), kernel, externalTriggerEvent, "Order 2");
        Console.WriteLine($"=== End SK Process '{processBuilder.Name}' ===");
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

        Console.WriteLine($"=== Start SK Process '{processBuilder.Name}' ===");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 2");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 3");
        Console.WriteLine($"=== End SK Process '{processBuilder.Name}' ===");
    }

    [Fact]
    public async Task UsePrepareStatefulPotatoFriesProcessSharedStateAsync()
    {
        var processBuilder = PotatoFriesProcess.CreateProcessWithStatefulSteps();
        var externalTriggerEvent = PotatoFriesProcess.ProcessEvents.PreparePotatoFries;

        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = processBuilder.Build();

        Console.WriteLine($"=== Start SK Process '{processBuilder.Name}' ===");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 2");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 3");
        Console.WriteLine($"=== End SK Process '{processBuilder.Name}' ===");
    }

    private async Task<KernelProcess> ExecuteProcessWithStateAsync(KernelProcess process, Kernel kernel, string externalTriggerEvent, string orderLabel = "Order 1")
    {
        Console.WriteLine($"=== {orderLabel} ===");
        var runningProcess = await process.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = externalTriggerEvent,
            Data = new List<string>()
        });
        return await runningProcess.GetStateAsync();
    }

    #region Running processes and saving Process State Metadata in a file locally
    [Fact]
    public async Task RunAndStoreStatefulFriedFishProcessStateAsync()
    {
        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder builder = FriedFishProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess friedFishProcess = builder.Build();

        var executedProcess = await ExecuteProcessWithStateAsync(friedFishProcess, kernel, externalTriggerEvent: FriedFishProcess.ProcessEvents.PrepareFriedFish);
        var processState = executedProcess.ToProcessStateMetadata();
        DumpProcessStateMetadataLocally(processState, _statefulFriedFishProcessFilename);
    }

    [Fact]
    public async Task RunAndStoreStatefulFishSandwichProcessStateAsync()
    {
        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder builder = FishSandwichProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess friedFishProcess = builder.Build();

        var executedProcess = await ExecuteProcessWithStateAsync(friedFishProcess, kernel, externalTriggerEvent: FishSandwichProcess.ProcessEvents.PrepareFishSandwich);
        var processState = executedProcess.ToProcessStateMetadata();
        DumpProcessStateMetadataLocally(processState, _statefulFishSandwichProcessFilename);
    }
    #endregion

    #region Reading State from local file and apply to existing ProcessBuilder
    [Fact]
    public async Task RunStatefulFriedFishProcessFromFileAsync()
    {
        var processState = LoadProcessStateMetadata(this._statefulFriedFishProcessFilename);
        Assert.NotNull(processState);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build(processState);

        await ExecuteProcessWithStateAsync(processFromFile, kernel, externalTriggerEvent: FriedFishProcess.ProcessEvents.PrepareFriedFish);
    }

    [Fact]
    public async Task RunStatefulFriedFishProcessWithLowStockFromFileAsync()
    {
        var processState = LoadProcessStateMetadata(this._statefulFriedFishLowStockProcessFilename);
        Assert.NotNull(processState);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build(processState);

        await ExecuteProcessWithStateAsync(processFromFile, kernel, externalTriggerEvent: FriedFishProcess.ProcessEvents.PrepareFriedFish);
    }

    [Fact]
    public async Task RunStatefulFriedFishProcessWithNoStockFromFileAsync()
    {
        var processState = LoadProcessStateMetadata(this._statefulFriedFishNoStockProcessFilename);
        Assert.NotNull(processState);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build(processState);

        await ExecuteProcessWithStateAsync(processFromFile, kernel, externalTriggerEvent: FriedFishProcess.ProcessEvents.PrepareFriedFish);
    }

    [Fact]
    public async Task RunStatefulFishSandwichProcessFromFileAsync()
    {
        var processState = LoadProcessStateMetadata(this._statefulFishSandwichProcessFilename);
        Assert.NotNull(processState);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FishSandwichProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build(processState);

        await ExecuteProcessWithStateAsync(processFromFile, kernel, externalTriggerEvent: FishSandwichProcess.ProcessEvents.PrepareFishSandwich);
    }

    [Fact]
    public async Task RunStatefulFishSandwichProcessWithLowStockFromFileAsync()
    {
        var processState = LoadProcessStateMetadata(this._statefulFishSandwichLowStockProcessFilename);
        Assert.NotNull(processState);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FishSandwichProcess.CreateProcessWithStatefulStepsV1();
        KernelProcess processFromFile = processBuilder.Build(processState);

        await ExecuteProcessWithStateAsync(processFromFile, kernel, externalTriggerEvent: FishSandwichProcess.ProcessEvents.PrepareFishSandwich);
    }

    #region Versioning compatibiily scenarios: Loading State generated with previous version of process
    [Fact]
    public async Task RunStatefulFriedFishV2ProcessWithLowStockV1StateFromFileAsync()
    {
        var processState = LoadProcessStateMetadata(this._statefulFriedFishLowStockProcessFilename);
        Assert.NotNull(processState);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FriedFishProcess.CreateProcessWithStatefulStepsV2();
        KernelProcess processFromFile = processBuilder.Build(processState);

        await ExecuteProcessWithStateAsync(processFromFile, kernel, externalTriggerEvent: FriedFishProcess.ProcessEvents.PrepareFriedFish);
    }

    [Fact]
    public async Task RunStatefulFishSandwichV2ProcessWithLowStockV1StateFromFileAsync()
    {
        var processState = LoadProcessStateMetadata(this._statefulFishSandwichLowStockProcessFilename);
        Assert.NotNull(processState);

        Kernel kernel = CreateKernelWithChatCompletion();
        ProcessBuilder processBuilder = FishSandwichProcess.CreateProcessWithStatefulStepsV2();
        KernelProcess processFromFile = processBuilder.Build(processState);

        await ExecuteProcessWithStateAsync(processFromFile, kernel, externalTriggerEvent: FishSandwichProcess.ProcessEvents.PrepareFishSandwich);
    }
    #endregion
    #endregion
    #endregion
    protected async Task UsePrepareSpecificProductAsync(ProcessBuilder processBuilder, string externalTriggerEvent)
    {
        // Arrange
        Kernel kernel = CreateKernelWithChatCompletion();

        // Act
        KernelProcess kernelProcess = processBuilder.Build();

        // Assert
        Console.WriteLine($"=== Start SK Process '{processBuilder.Name}' ===");
        await using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = externalTriggerEvent, Data = new List<string>()
        });
        Console.WriteLine($"=== End SK Process '{processBuilder.Name}' ===");
    }

    // Step03a Utils for saving and loading SK Processes from/to repository
    private readonly string _step03RelativePath = Path.Combine("Step03", "ProcessesStates");
    private readonly string _statefulFriedFishProcessFilename = "FriedFishProcessStateSuccess.json";
    private readonly string _statefulFriedFishLowStockProcessFilename = "FriedFishProcessStateSuccessLowStock.json";
    private readonly string _statefulFriedFishNoStockProcessFilename = "FriedFishProcessStateSuccessNoStock.json";
    private readonly string _statefulFishSandwichProcessFilename = "FishSandwichStateProcessSuccess.json";
    private readonly string _statefulFishSandwichLowStockProcessFilename = "FishSandwichStateProcessSuccessLowStock.json";

    private void DumpProcessStateMetadataLocally(KernelProcessStateMetadata processStateInfo, string jsonFilename)
    {
        var sampleRelativePath = GetSampleStep03Filepath(jsonFilename);
        ProcessStateMetadataUtilities.DumpProcessStateMetadataLocally(processStateInfo, sampleRelativePath);
    }

    private KernelProcessStateMetadata? LoadProcessStateMetadata(string jsonFilename)
    {
        var sampleRelativePath = GetSampleStep03Filepath(jsonFilename);
        return ProcessStateMetadataUtilities.LoadProcessStateMetadata(sampleRelativePath);
    }

    private string GetSampleStep03Filepath(string jsonFilename)
    {
        return Path.Combine(this._step03RelativePath, jsonFilename);
    }
}
