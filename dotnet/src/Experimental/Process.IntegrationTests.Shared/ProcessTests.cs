// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System;
using System.Linq;
using System.Runtime.Serialization;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using SemanticKernel.Process.TestsShared.Steps;
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
        this.AssertStepStateLastMessage(processInfo, nameof(RepeatStep), expectedLastMessage: string.Join(" ", Enumerable.Repeat(testInput, 2)));
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
        this.AssertStepStateLastMessage(innerProcess, nameof(RepeatStep), expectedLastMessage: string.Join(" ", Enumerable.Repeat(testInput, 4)));
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
        this.AssertStepStateLastMessage(processInfo, nameof(RepeatStep), expectedLastMessage: string.Join(" ", Enumerable.Repeat(testInput, 4)));
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
        this.AssertStepStateLastMessage(processInfo, nameof(RepeatStep), expectedLastMessage: null);
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
        this.AssertStepStateLastMessage(processInfo, nameof(FanInStep), expectedLastMessage: $"{testInput}-{testInput} {testInput}");
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
        this.AssertStepStateLastMessage(processInfo, nameof(ReportStep), expectedLastMessage: null, expectedInvocationCount: 1);
        this.AssertStepStateLastMessage(processInfo, nameof(RepeatStep), expectedLastMessage: null);
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
        var subprocessStepInfo = processInfo.Steps.Where(s => s.State.Name == fanInStepName)?.FirstOrDefault() as KernelProcess;
        Assert.NotNull(subprocessStepInfo);
        this.AssertStepStateLastMessage(subprocessStepInfo, nameof(FanInStep), expectedLastMessage: $"{testInput}-{testInput} {testInput}");
    }

    /// <summary>
    /// Process with multiple "long" nested sequential subprocesses and with multiple single step
    /// output fan out only steps
    /// <code>
    ///            ┌───────────────────────────────────────────────┐
    ///            │                                               ▼
    /// ┌───────┐  │   ┌──────────────┐     ┌──────────────┐    ┌──────┐
    /// │  1st  ├──┼──►│  2nd-nested  ├──┬─►│  3rd-nested  ├─┬─►│ last │
    /// └───────┘  │   └──────────────┘  │  └──────────────┘ │  └──────┘
    ///            ▼                     ▼                   ▼
    ///       ┌─────────┐           ┌─────────┐         ┌─────────┐
    ///       │ output1 │           │ output2 │         │ output3 │
    ///       └─────────┘           └─────────┘         └─────────┘
    /// </code>
    /// </summary>
    /// <returns><see cref="Task"/></returns>
    [Fact]
    public async Task ProcessWith2NestedSubprocessSequentiallyAndMultipleOutputStepsAsync()
    {
        // Arrange
        Kernel kernel = this._kernelBuilder.Build();
        string lastStepName = "lastEmitterStep";
        string outputStepName1 = "outputStep1";
        string outputStepName2 = "outputStep2";
        string outputStepName3 = "outputStep3";
        ProcessBuilder processBuilder = new(nameof(ProcessWith2NestedSubprocessSequentiallyAndMultipleOutputStepsAsync));

        ProcessStepBuilder firstStep = processBuilder.AddStepFromType<EmitterStep>("firstEmitterStep");
        ProcessBuilder secondStep = processBuilder.AddStepFromProcess(this.CreateLongSequentialProcessWithFanInAsOutputStep("subprocess1"));
        ProcessBuilder thirdStep = processBuilder.AddStepFromProcess(this.CreateLongSequentialProcessWithFanInAsOutputStep("subprocess2"));
        ProcessStepBuilder outputStep1 = processBuilder.AddStepFromType<EmitterStep>(outputStepName1);
        ProcessStepBuilder outputStep2 = processBuilder.AddStepFromType<EmitterStep>(outputStepName2);
        ProcessStepBuilder outputStep3 = processBuilder.AddStepFromType<EmitterStep>(outputStepName3);
        ProcessStepBuilder lastStep = processBuilder.AddStepFromType<FanInStep>(lastStepName);

        processBuilder
            .OnInputEvent(EmitterStep.InputEvent)
            .SendEventTo(new ProcessFunctionTargetBuilder(firstStep, functionName: EmitterStep.InternalEventFunction));
        firstStep
            .OnEvent(EmitterStep.EventId)
            .SendEventTo(secondStep.WhereInputEventIs(EmitterStep.InputEvent))
            .SendEventTo(new ProcessFunctionTargetBuilder(outputStep1, functionName: EmitterStep.PublicEventFunction));
        secondStep
            .OnEvent(ProcessTestsEvents.OutputReadyPublic)
            .SendEventTo(thirdStep.WhereInputEventIs(EmitterStep.InputEvent))
            .SendEventTo(new ProcessFunctionTargetBuilder(outputStep2, functionName: EmitterStep.PublicEventFunction));
        thirdStep
            .OnEvent(ProcessTestsEvents.OutputReadyPublic)
            .SendEventTo(new ProcessFunctionTargetBuilder(lastStep, parameterName: "secondInput"))
            .SendEventTo(new ProcessFunctionTargetBuilder(outputStep3, functionName: EmitterStep.PublicEventFunction));

        firstStep
            .OnEvent(EmitterStep.EventId)
            .SendEventTo(new ProcessFunctionTargetBuilder(lastStep, parameterName: "firstInput"));

        KernelProcess process = processBuilder.Build();

        // Act
        string testInput = "SomeData";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new KernelProcessEvent() { Id = EmitterStep.InputEvent, Data = testInput });
        var processInfo = await processHandle.GetStateAsync();

        // Assert
        this.AssertStepStateLastMessage(processInfo, outputStepName1, expectedLastMessage: testInput);
        this.AssertStepStateLastMessage(processInfo, outputStepName2, expectedLastMessage: $"{testInput}-{testInput}");
        this.AssertStepStateLastMessage(processInfo, outputStepName3, expectedLastMessage: $"{testInput}-{testInput}-{testInput}-{testInput}");
        this.AssertStepStateLastMessage(processInfo, lastStepName, expectedLastMessage: $"{testInput}-{testInput}-{testInput}-{testInput}-{testInput}");
    }

    #region Predefined ProcessBuilders for testing
    /// <summary>
    /// Sample long sequential process, each step has a delay.<br/>
    /// Input Event: <see cref="EmitterStep.InputEvent"/><br/>
    /// Output Event: <see cref="ProcessTestsEvents.OutputReadyPublic"/><br/>
    /// <code>
    ///            ┌───────────────────────────────────────────────┐
    ///            │                                               ▼
    /// ┌───────┐  │   ┌───────┐    ┌───────┐    ┌────────┐    ┌──────┐
    /// │  1st  ├──┴──►│  2nd  ├───►│  ...  ├───►│  10th  ├───►│ last │
    /// └───────┘      └───────┘    └───────┘    └────────┘    └──────┘
    /// </code>
    /// </summary>
    /// <param name="name">name of the process</param>
    /// <returns><see cref="ProcessBuilder"/></returns>
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
        ninthNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(tenthNestedStep, functionName: EmitterStep.DualInputPublicEventFunction, parameterName: "secondInput"));

        firstNestedStep.OnEvent(EmitterStep.EventId).SendEventTo(new ProcessFunctionTargetBuilder(tenthNestedStep, functionName: EmitterStep.DualInputPublicEventFunction, parameterName: "firstInput"));

        return processBuilder;
    }

    /// <summary>
    /// Creates a simple linear process with two steps.<br/>
    /// Input Event: <see cref="ProcessTestsEvents.StartProcess"/><br/>
    /// Output Events: [<see cref="ProcessTestsEvents.OutputReadyInternal"/>, <see cref="ProcessTestsEvents.OutputReadyPublic"/>]<br/>
    /// <code>
    /// ┌────────┐    ┌────────┐
    /// │  echo  ├───►│ repeat │
    /// └────────┘    └────────┘
    /// </code>
    /// </summary>
    private ProcessBuilder CreateLinearProcess(string name)
    {
        var processBuilder = new ProcessBuilder(name);
        var echoStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>();
        var repeatStep = processBuilder.AddStepFromType<RepeatStep>();

        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        echoStep.OnFunctionResult(nameof(CommonSteps.EchoStep.Echo))
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatStep, parameterName: "message"));

        return processBuilder;
    }

    /// <summary>
    /// Simple process with fan in functionality.<br/>
    /// Input Event: <see cref="ProcessTestsEvents.StartProcess"/><br/>
    /// Output Events: <see cref="ProcessTestsEvents.OutputReadyPublic"/><br/>
    /// <code>
    /// ┌─────────┐
    /// │  echoA  ├──────┐
    /// └─────────┘      ▼
    ///              ┌────────┐
    ///              │ fanInC │
    ///              └────────┘
    /// ┌─────────┐      ▲
    /// │ repeatB ├──────┘
    /// └─────────┘
    /// </code>
    /// </summary>
    /// <param name="name">name of the process</param>
    /// <returns><see cref="ProcessBuilder"/></returns>
    private ProcessBuilder CreateFanInProcess(string name)
    {
        var processBuilder = new ProcessBuilder(name);
        var echoAStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>("EchoStepA");
        var repeatBStep = processBuilder.AddStepFromType<RepeatStep>("RepeatStepB");
        var fanInCStep = processBuilder.AddStepFromType<FanInStep>();

        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess).SendEventTo(new ProcessFunctionTargetBuilder(echoAStep));
        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess).SendEventTo(new ProcessFunctionTargetBuilder(repeatBStep, parameterName: "message"));

        echoAStep.OnFunctionResult(nameof(CommonSteps.EchoStep.Echo)).SendEventTo(new ProcessFunctionTargetBuilder(fanInCStep, parameterName: "firstInput"));
        repeatBStep.OnEvent(ProcessTestsEvents.OutputReadyPublic).SendEventTo(new ProcessFunctionTargetBuilder(fanInCStep, parameterName: "secondInput"));

        return processBuilder;
    }

    /// <summary>
    /// Creates a simple linear process with that emit error events.<br/>
    /// Input Event: <see cref="ProcessTestsEvents.StartProcess"/><br/>
    /// Output Events: <see cref="ProcessStepBuilder.OnFunctionError(string?)"/> <br/>
    /// <code>
    ///               ┌────────┐
    ///      ┌───────►│ repeat │
    ///      │        └────────┘
    ///  ┌───┴───┐
    ///  │ error │
    ///  └───┬───┘
    ///      │        ┌────────┐
    ///      └───────►│ report │
    ///               └────────┘
    /// </code>
    /// </summary>
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
    #endregion
    #region Assert Utils
    private void AssertStepStateLastMessage(KernelProcess processInfo, string stepName, string? expectedLastMessage, int? expectedInvocationCount = null)
    {
        KernelProcessStepInfo? stepInfo = processInfo.Steps.FirstOrDefault(s => s.State.Name == stepName);
        Assert.NotNull(stepInfo);
        var outputStepResult = stepInfo.State as KernelProcessStepState<StepState>;
        Assert.NotNull(outputStepResult?.State);
        Assert.Equal(expectedLastMessage, outputStepResult.State.LastMessage);
        if (expectedInvocationCount.HasValue)
        {
            Assert.Equal(expectedInvocationCount.Value, outputStepResult.State.InvocationCount);
        }
    }
    #endregion
}
