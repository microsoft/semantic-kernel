// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System;
using System.Linq;
using System.Runtime.Serialization;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
#pragma warning restore IDE0005 // Using directive is unnecessary.

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Integration tests for processes.
/// </summary>
[Collection(nameof(ProcessTestGroup))]
public sealed class ProcessTests : IClassFixture<ProcessTestFixture>
{
    private readonly ProcessTestFixture _fixture;
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIConfiguration>()
            .Build();

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessTests"/> class. This is called by the test framework.
    /// </summary>
    /// <param name="fixture"></param>
    public ProcessTests(ProcessTestFixture fixture)
    {
        this._fixture = fixture;
    }

    /// <summary>
    /// Tests a simple linear process with two steps and no sub processes.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task LinearProcessAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();
        var process = this.CreateLinearProcess("Simple").Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        var repeatStepState = processInfo.Steps.Where(s => s.State.Name == nameof(RepeatStep)).FirstOrDefault()?.State as KernelProcessStepState<StepState>;
        Assert.NotNull(repeatStepState?.State);
        Assert.Equal(string.Join(" ", Enumerable.Repeat(testInput, 2)), repeatStepState.State.LastMessage);
    }

    /// <summary>
    /// Tests a process with three steps where the third step is a nested process. Ev/ts from the outer process
    /// are routed to the inner process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task NestedProcessOuterToInnerWorksAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();

        // Create the outer process
        var processBuilder = this.CreateLinearProcess("Outer");

        // Create the inner process and add it as a step to the outer process
        var nestedProcessStep = processBuilder.AddStepFromProcess(this.CreateLinearProcess("Inner"));

        // Route the last step of the outer process to trigger the external event that starts the inner process
        processBuilder.Steps[1].OnEvent(ProcessTestsEvents.OutputReadyInternal)
            .SendEventTo(nestedProcessStep.WhereInputEventIs(ProcessTestsEvents.StartProcess));

        // Build the outer process
        var process = processBuilder.Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        var innerProcess = processInfo.Steps.Where(s => s.State.Name == "Inner").Single() as KernelProcess;
        Assert.NotNull(innerProcess);
        var repeatStepState = innerProcess.Steps.Where(s => s.State.Name == nameof(RepeatStep)).Single().State as KernelProcessStepState<StepState>;
        Assert.NotNull(repeatStepState?.State);
        Assert.Equal(string.Join(" ", Enumerable.Repeat(testInput, 4)), repeatStepState.State.LastMessage);
    }

    /// <summary>
    /// Tests a process with three steps where the third step is a nested process. Events from the inner process
    /// are routed to the outer process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task NestedProcessInnerToOuterWorksWithPublicEventAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();

        // Create the outer process
        var processBuilder = this.CreateLinearProcess("Outer");

        // Create the inner process and add it as a step to the outer process
        var nestedProcessStep = processBuilder.AddStepFromProcess(this.CreateLinearProcess("Inner"));

        // Add a new external event to start the outer process and handoff to the inner process directly
        processBuilder.OnInputEvent(ProcessTestsEvents.StartInnerProcess)
            .SendEventTo(nestedProcessStep.WhereInputEventIs(ProcessTestsEvents.StartProcess));

        // Route the last step of the inner process to trigger the echo step of the outer process
        nestedProcessStep.OnEvent(ProcessTestsEvents.OutputReadyPublic)
            .SendEventTo(new ProcessFunctionTargetBuilder(processBuilder.Steps[0]));

        // Build the outer process
        var process = processBuilder.Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartInnerProcess, Data = testInput });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        var repeatStepState = processInfo.Steps.Where(s => s.State.Name == nameof(RepeatStep)).FirstOrDefault()?.State as KernelProcessStepState<StepState>;
        Assert.NotNull(repeatStepState?.State);
        Assert.Equal(string.Join(" ", Enumerable.Repeat(testInput, 4)), repeatStepState.State.LastMessage);
    }

    /// <summary>
    /// Tests a process with three steps where the third step is a nested process. Events from the inner process
    /// are routed to the outer process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task NestedProcessInnerToOuterDoesNotWorkWithInternalEventAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();

        // Create the outer process
        var processBuilder = this.CreateLinearProcess("Outer");

        // Create the inner process and add it as a step to the outer process
        var nestedProcessStep = processBuilder.AddStepFromProcess(this.CreateLinearProcess("Inner"));

        // Add a new external event to start the outer process and handoff to the inner process directly
        processBuilder.OnInputEvent(ProcessTestsEvents.StartInnerProcess)
            .SendEventTo(nestedProcessStep.WhereInputEventIs(ProcessTestsEvents.StartProcess));

        // Route the last step of the inner process to trigger the echo step of the outer process
        nestedProcessStep.OnEvent(ProcessTestsEvents.OutputReadyInternal)
            .SendEventTo(new ProcessFunctionTargetBuilder(processBuilder.Steps[0]));

        // Build the outer process
        var process = processBuilder.Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartInnerProcess, Data = testInput });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        var repeatStepState = processInfo.Steps.Where(s => s.State.Name == nameof(RepeatStep)).FirstOrDefault()?.State as KernelProcessStepState<StepState>;
        Assert.NotNull(repeatStepState);
        Assert.Null(repeatStepState.State?.LastMessage);
    }

    /// <summary>
    /// Test with a fan in process where the same event triggers 2 steps inside the process that then connect to a step that expects
    /// the outputs of these steps
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task FanInProcessAsync()
    {
        // Arrange
        Kernel kernel = this._kernelBuilder.Build();
        var process = this.CreateFanInProcess("FanIn").Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        var outputStep = processInfo.Steps.Where(s => s.State.Name == nameof(FanInStep)).FirstOrDefault()?.State as KernelProcessStepState<StepState>;
        Assert.NotNull(outputStep?.State);
        Assert.Equal($"{testInput}-{testInput} {testInput}", outputStep.State.LastMessage);
    }

    /// <summary>
    /// Test with a process that has an error step that emits an error event
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task ProcessWithErrorEmitsErrorEventAsync()
    {
        // Arrange
        Kernel kernel = this._kernelBuilder.Build();
        var process = this.CreateProcessWithError("ProcessWithError").Build();

        // Act
        bool shouldError = true;
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = shouldError });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        var reportStep = processInfo.Steps.Where(s => s.State.Name == nameof(ReportStep)).FirstOrDefault()?.State as KernelProcessStepState<StepState>;
        Assert.NotNull(reportStep?.State);
        Assert.Equal(1, reportStep.State.InvocationCount);

        var repeatStep = processInfo.Steps.Where(s => s.State.Name == nameof(RepeatStep)).FirstOrDefault()?.State as KernelProcessStepState<StepState>;
        Assert.NotNull(repeatStep?.State);
        Assert.Null(repeatStep.State.LastMessage);
    }

    /// <summary>
    /// Test with a single step that then connects to a nested fan in process with 2 input steps
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task StepAndFanInProcessAsync()
    {
        // Arrange
        Kernel kernel = this._kernelBuilder.Build();
        var processBuilder = new ProcessBuilder("StepAndFanIn");
        var startStep = processBuilder.AddStepFromType<StartStep>();
        var fanInStepName = "InnerFanIn";
        var fanInStep = processBuilder.AddStepFromProcess(this.CreateFanInProcess(fanInStepName));

        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess).SendEventTo(new ProcessFunctionTargetBuilder(startStep));
        startStep.OnEvent(ProcessTestsEvents.StartProcess).SendEventTo(fanInStep.WhereInputEventIs(ProcessTestsEvents.StartProcess));
        var process = processBuilder.Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        var outputStep = (processInfo.Steps.Where(s => s.State.Name == fanInStepName).FirstOrDefault() as KernelProcess)?.Steps.Where(s => s.State.Name == nameof(FanInStep)).FirstOrDefault()?.State as KernelProcessStepState<StepState>;
        Assert.NotNull(outputStep?.State);
        Assert.Equal($"{testInput}-{testInput} {testInput}", outputStep.State.LastMessage);
    }

    /// <summary>
    ///            ┌───────────────────────────────────────────────┐
    ///            │                                               ▼
    /// ┌───────┐  │   ┌──────────────┐     ┌──────────────┐    ┌──────┐
    /// │  1st  ├──┼──►│  2nd-nested  ├──┬─►│  3rd-nested  ├───►│ last │
    /// └───────┘  │   └──────────────┘  │  └──────────────┘    └──────┘
    ///            ▼                     ▼
    ///        ┌───────┐             ┌───────┐
    ///        │  4th  │             │  5th  │
    ///        └───────┘             └───────┘
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task ProcessWith2NestedSubprocessSequentiallyAndMultipleOutputStepsAsync()
    {
        // Arrange
        Kernel kernel = this._kernelBuilder.Build();
        string lastStepName = "lastEmitterStep";
        ProcessBuilder processBuilder = new(nameof(ProcessWith2NestedSubprocessSequentiallyAndMultipleOutputStepsAsync));

        ProcessStepBuilder firstStep = processBuilder.AddStepFromType<EmitterStep>("firstEmitterStep");
        ProcessBuilder secondStep = processBuilder.AddStepFromProcess(this.CreateLongSequentialProcessWithFanInAsOutputStep("subprocess1"));
        ProcessBuilder thirdStep = processBuilder.AddStepFromProcess(this.CreateLongSequentialProcessWithFanInAsOutputStep("subprocess2"));
        ProcessStepBuilder fourthStep = processBuilder.AddStepFromType<EmitterStep>("fourthStep");
        ProcessStepBuilder fifthStep = processBuilder.AddStepFromType<EmitterStep>("fifthStep");
        ProcessStepBuilder lastStep = processBuilder.AddStepFromType<FanInStep>(lastStepName);

        processBuilder
            .OnInputEvent(EmitterStep.InputEvent)
            .SendEventTo(new ProcessFunctionTargetBuilder(firstStep, functionName: EmitterStep.InternalEventFunction));
        firstStep
            .OnEvent(EmitterStep.EventId)
            .SendEventTo(secondStep.WhereInputEventIs(EmitterStep.InputEvent));
        secondStep
            .OnEvent(ProcessTestsEvents.OutputReadyPublic)
            .SendEventTo(new ProcessFunctionTargetBuilder(fourthStep, functionName: EmitterStep.PublicEventFunction))
            .SendEventTo(thirdStep.WhereInputEventIs(EmitterStep.InputEvent));

        firstStep
            .OnEvent(EmitterStep.EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(lastStep, parameterName: "firstInput"));
        thirdStep
            .OnEvent(ProcessTestsEvents.OutputReadyPublic)
            .SendEventTo(new ProcessFunctionTargetBuilder(lastStep, parameterName: "secondInput"))
            .SendEventTo(new ProcessFunctionTargetBuilder(fifthStep, functionName: EmitterStep.PublicEventFunction));

        KernelProcess process = processBuilder.Build();

        // Act
        string testInput = "SomeData";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new KernelProcessEvent() { Id = EmitterStep.InputEvent, Data = testInput });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        var outputStep = (processInfo.Steps.Where(s => s.State.Name == lastStepName).FirstOrDefault() as KernelProcessStepInfo).State as KernelProcessStepState<StepState>;
        Assert.NotNull(outputStep?.State);
        Assert.NotNull(outputStep?.State.LastMessage);
        Assert.Equal($"{testInput}-{testInput}-{testInput}-{testInput}-{testInput}", outputStep.State.LastMessage);
    }

    private ProcessBuilder CreateLongSequentialProcessWithFanInAsOutputStep(string name)
    {
        ProcessBuilder processBuilder = new(name);
        ProcessStepBuilder firstNestedStep = processBuilder.AddStepFromType<EmitterStep>("firstNestedStep");
        ProcessStepBuilder secondNestedStep = processBuilder.AddStepFromType<EmitterStep>("secondNestedStep");
        ProcessStepBuilder thirdNestedStep = processBuilder.AddStepFromType<EmitterStep>("thirdNestedStep");
        ProcessStepBuilder fourthNestedStep = processBuilder.AddStepFromType<EmitterStep>("fourthNestedStep");
        ProcessStepBuilder fifthNestedStep = processBuilder.AddStepFromType<EmitterStep>("fifthNestedStep");
        ProcessStepBuilder sixthNestedStep = processBuilder.AddStepFromType<EmitterStep>("sixthNestedStep");
        ProcessStepBuilder seventhNestedStep = processBuilder.AddStepFromType<EmitterStep>("seventhNestedStep");
        ProcessStepBuilder eighthNestedStep = processBuilder.AddStepFromType<EmitterStep>("eighthNestedStep");
        ProcessStepBuilder ninthNestedStep = processBuilder.AddStepFromType<EmitterStep>("ninthNestedStep");
        ProcessStepBuilder tenthNestedStep = processBuilder.AddStepFromType<EmitterStep>("tenthNestedStep");

        processBuilder.OnInputEvent(EmitterStep.InputEvent).SendEventTo(new ProcessFunctionTargetBuilder(firstNestedStep, functionName: EmitterStep.InternalEventFunction));
        firstNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(secondNestedStep, functionName: EmitterStep.InternalEventFunction));
        secondNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(thirdNestedStep, functionName: EmitterStep.InternalEventFunction));
        thirdNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(fourthNestedStep, functionName: EmitterStep.InternalEventFunction));
        fourthNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(fifthNestedStep, functionName: EmitterStep.InternalEventFunction));
        fifthNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(sixthNestedStep, functionName: EmitterStep.InternalEventFunction));
        sixthNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(seventhNestedStep, functionName: EmitterStep.InternalEventFunction));
        seventhNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(eighthNestedStep, functionName: EmitterStep.InternalEventFunction));
        eighthNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(ninthNestedStep, functionName: EmitterStep.InternalEventFunction));
        firstNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(tenthNestedStep, functionName: EmitterStep.DualInputPublicEventFunction, parameterName: "firstInput"));
        ninthNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(tenthNestedStep, functionName: EmitterStep.DualInputPublicEventFunction, parameterName: "secondInput"));

        return processBuilder;
    }

    /// <summary>
    /// Creates a simple linear process with two steps.
    /// </summary>
    private ProcessBuilder CreateLinearProcess(string name)
    {
        var processBuilder = new ProcessBuilder(name);
        var echoStep = processBuilder.AddStepFromType<EchoStep>();
        var repeatStep = processBuilder.AddStepFromType<RepeatStep>();

        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        echoStep.OnFunctionResult(nameof(EchoStep.Echo))
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatStep, parameterName: "message"));

        return processBuilder;
    }

    private ProcessBuilder CreateFanInProcess(string name)
    {
        var processBuilder = new ProcessBuilder(name);
        var echoAStep = processBuilder.AddStepFromType<EchoStep>("EchoStepA");
        var repeatBStep = processBuilder.AddStepFromType<RepeatStep>("RepeatStepB");
        var fanInCStep = processBuilder.AddStepFromType<FanInStep>();
        var echoDStep = processBuilder.AddStepFromType<EchoStep>();

        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess).SendEventTo(new ProcessFunctionTargetBuilder(echoAStep));
        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess).SendEventTo(new ProcessFunctionTargetBuilder(repeatBStep, parameterName: "message"));

        echoAStep.OnFunctionResult(nameof(EchoStep.Echo)).SendEventTo(new ProcessFunctionTargetBuilder(fanInCStep, parameterName: "firstInput"));
        repeatBStep.OnEvent(ProcessTestsEvents.OutputReadyPublic).SendEventTo(new ProcessFunctionTargetBuilder(fanInCStep, parameterName: "secondInput"));

        return processBuilder;
    }

    private ProcessBuilder CreateProcessWithError(string name)
    {
        var processBuilder = new ProcessBuilder(name);
        var errorStep = processBuilder.AddStepFromType<ErrorStep>("ErrorStep");
        var repeatStep = processBuilder.AddStepFromType<RepeatStep>("RepeatStep");
        var reportStep = processBuilder.AddStepFromType<ReportStep>("ReportStep");

        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess).SendEventTo(new ProcessFunctionTargetBuilder(errorStep));
        errorStep.OnEvent(ProcessTestsEvents.ErrorStepSuccess).SendEventTo(new ProcessFunctionTargetBuilder(repeatStep, parameterName: "message"));
        errorStep.OnFunctionError("ErrorWhenTrue").SendEventTo(new ProcessFunctionTargetBuilder(reportStep));

        return processBuilder;
    }
}
