﻿// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.IntegrationTests.TestSettings;
using Microsoft.SemanticKernel.Process.TestsShared.Steps;
using Xunit;
#pragma warning restore IDE0005 // Using directive is unnecessary.

namespace Microsoft.SemanticKernel.Process.IntegrationTests;

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
    /// Tests a simple process with a WhenAll event listener
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task ProcessWithWhenAllListenerAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();
        var process = this.GetProcess().Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, new(), new() { Id = ProcessTestsEvents.StartProcess, Data = testInput }, runId: Guid.NewGuid().ToString());

        var processInfo = await processHandle.GetStateAsync();

        // Assert
        this.AssertStepState(processInfo, "cStep", (KernelProcessStepState<CStepState> state) => state.State?.CurrentCycle == 3);
    }

    /// <summary>
    /// Tests a process with a WhenAll listener and a step that has multiple functions and parameters.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task ProcessWithWhenAllListenerAndStepWithMultipleFunctionsAndParametersUsingOnlyOneMultiParamFunctionAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();

        var processBuilder = this.CreateProcessWithFanInUsingStepWithMultipleFunctionsAndParameters("testProcess");
        var process = processBuilder.Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput });

        // Assert
        var processInfo = await processHandle.GetStateAsync();
        this.AssertStepStateLastMessage(processInfo, "emitterStep", expectedLastMessage: $"{testInput} {testInput}-{testInput}");
    }

    /// <summary>
    /// Tests a process with a WhenAll listener and a step that has multiple functions and parameters.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task ProcessWithWhenAllListenerAndStepWithMultipleFunctionsAndParametersUsingOnlyTwoMultiParamFunctionsFromStepsAndInputEventsAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();

        var processBuilder = this.CreateProcessWithFanInUsingStepWithMultipleFunctionsAndParametersSimultaneouslyFromStepsAndInputEvents("testProcess");
        var process = processBuilder.Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput });

        // Assert
        var processInfo = await processHandle.GetStateAsync();
        this.AssertStepStateLastMessage(processInfo, "fanInStep", expectedLastMessage: $"{testInput}-{testInput}-{testInput} {testInput}-{testInput}-thirdInput-someFixedInputFromProcessDefinition");
    }

    /// <summary>
    /// Tests a process with a WhenAll listener and a step that has multiple functions and parameters.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task ProcessWithWhenAllListenerAndStepWithMultipleFunctionsAndParametersUsingOnlyTwoMultiParamFunctionsFromStepsOnlyAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();

        var processBuilder = this.CreateProcessWithFanInUsingStepWithMultipleFunctionsAndParametersSimultaneouslyFromStepsOnly("testProcess");
        var process = processBuilder.Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput });

        // Assert
        var processInfo = await processHandle.GetStateAsync();
        this.AssertStepStateLastMessage(processInfo, "fanInStep", expectedLastMessage: $"{testInput} {testInput}-{testInput}-{testInput} {testInput}-{testInput}-thirdInput-someFixedInputFromProcessDefinition");
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
        var innerProcess = processInfo.Steps.Where(s => s.State.StepId == "Inner").Single() as KernelProcess;
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
        var startStep = processBuilder.AddStepFromType<StartStep>(id: "startStep");
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
        var subprocessStepInfo = processInfo.Steps.Where(s => s.State.StepId == fanInStepName)?.FirstOrDefault() as KernelProcess;
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
            .SendEventTo(new ProcessFunctionTargetBuilder(outputStep3, functionName: EmitterStep.PublicEventFunction));

        processBuilder.ListenFor().AllOf(
            [
                new(EmitterStep.EventId, firstStep),
                new(ProcessTestsEvents.OutputReadyPublic, thirdStep)
            ])
            .SendEventTo(new ProcessStepTargetBuilder(lastStep, inputMapping: (inputEvents) =>
            {
                // Map the inputs to the last step.
                return new()
                {
                    { "firstInput", inputEvents[firstStep.GetFullEventId(EmitterStep.EventId)] },
                    { "secondInput", inputEvents[thirdStep.GetFullEventId(ProcessTestsEvents.OutputReadyPublic)] }
                };
            }));

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

    private ProcessBuilder GetProcess()
    {
        // Create the process builder.
        ProcessBuilder processBuilder = new("ProcessWithDapr");

        // Add some steps to the process.
        var kickoffStep = processBuilder.AddStepFromType<KickoffStep>(id: "kickoffStep");
        var myAStep = processBuilder.AddStepFromType<AStep>(id: "aStep");
        var myBStep = processBuilder.AddStepFromType<BStep>(id: "bStep");

        // ########## Configuring initial state on steps in a process ###########
        // For demonstration purposes, we add the CStep and configure its initial state with a CurrentCycle of 1.
        // Initializing state in a step can be useful for when you need a step to start out with a predetermines
        // configuration that is not easily accomplished with dependency injection.
        var myCStep = processBuilder.AddStepFromType<CStep, CStepState>(initialState: new() { CurrentCycle = 1 }, id: "cStep");

        // Setup the input event that can trigger the process to run and specify which step and function it should be routed to.
        processBuilder
            .OnInputEvent(CommonEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        // When the kickoff step is finished, trigger both AStep and BStep.
        kickoffStep
            .OnEvent(CommonEvents.StartARequested)
            .SendEventTo(new ProcessFunctionTargetBuilder(myAStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(myBStep));

        // When step A and step B have finished, trigger the CStep.
        processBuilder
            .ListenFor()
                .AllOf(new()
                {
                    new(messageType: CommonEvents.AStepDone, source: myAStep),
                    new(messageType: CommonEvents.BStepDone, source: myBStep)
                })
                .SendEventTo(new ProcessStepTargetBuilder(myCStep, inputMapping: (inputEvents) =>
                {
                    // Map the input events to the CStep's input parameters.
                    // In this case, we are mapping the output of AStep to the first input parameter of CStep
                    // and the output of BStep to the second input parameter of CStep.
                    return new()
                    {
                        { "astepdata", inputEvents[$"aStep.{CommonEvents.AStepDone}"] },
                        { "bstepdata", inputEvents[$"bStep.{CommonEvents.BStepDone}"] }
                    };
                }));

        // When CStep has finished without requesting an exit, activate the Kickoff step to start again.
        myCStep
            .OnEvent(CommonEvents.CStepDone)
            .SendEventTo(new ProcessFunctionTargetBuilder(kickoffStep));

        // When the CStep has finished by requesting an exit, stop the process.
        myCStep
            .OnEvent(CommonEvents.ExitRequested)
            .StopProcess();

        return processBuilder;
    }

    /// <summary>
    /// Sample process with a fan in step that takes the output of two steps and combines them.<br/>
    /// Fan in step - emitter - has multiple functions and some have multiple parameters.<br/>
    /// <code>
    /// ┌────────┐
    /// │ repeat ├───┐
    /// └────────┘   │   ┌─────────┐
    ///              └──►│         │
    ///                  │ emitter │
    ///              ┌──►│         │
    /// ┌────────┐   │   └─────────┘
    /// │  echo  ├───┘
    /// └────────┘
    /// </code>
    /// </summary>
    /// <param name="name"></param>
    /// <returns></returns>
    private ProcessBuilder CreateProcessWithFanInUsingStepWithMultipleFunctionsAndParameters(string name)
    {
        ProcessBuilder processBuilder = new(name);
        ProcessStepBuilder repeatStep = processBuilder.AddStepFromType<RepeatStep>("repeatStep");
        ProcessStepBuilder echoStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>("echoStep");
        ProcessStepBuilder emitterStep = processBuilder.AddStepFromType<EmitterStep>("emitterStep");

        processBuilder
            .OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        processBuilder.ListenFor().AllOf(
            [
                new(ProcessTestsEvents.OutputReadyInternal, repeatStep),
                new(echoStep.GetFunctionResultEventId(), echoStep)
            ])
            .SendEventTo(new ProcessStepTargetBuilder(emitterStep, functionName: EmitterStep.DualInputPublicEventFunction, inputMapping: inputEvents =>
            {
                return new()
                {
                    { "firstInput", inputEvents[repeatStep.GetFullEventId(ProcessTestsEvents.OutputReadyInternal)] },
                    { "secondInput", inputEvents[echoStep.GetFullEventId()] }
                };
            }));

        return processBuilder;
    }

    /// <summary>
    /// Sample process with a fan in step that takes the output of two steps from same step and combines them.<br/>
    /// Fan in step - emitter - has multiple functions and some have multiple parameters.<br/>
    /// This test is meant to test the ability to create multiple internal edgeGroups in the same step.<br/>
    /// <code>
    /// ┌────────┐
    /// │ repeat ├───┐
    /// └────────┘   │ ┌────────┐  ┌─────────┐     ┌─────────┐
    ///              └►│ r_echo ├─►│         ├────►│         │
    ///                └────────┘  │ emitter │     │  fanIn  │
    ///              ┌-───────────►│         ├────►│         │
    /// ┌────────┐   │             └─────────┘     └─────────┘
    /// │  echo  ├───┘
    /// └────────┘
    /// </code>
    /// </summary>
    /// <param name="name"></param>
    /// <returns></returns>
    private ProcessBuilder CreateProcessWithFanInUsingStepWithMultipleFunctionsAndParametersSimultaneouslyFromStepsAndInputEvents(string name)
    {
        ProcessBuilder processBuilder = new(name);
        ProcessStepBuilder repeatStep = processBuilder.AddStepFromType<RepeatStep>("repeatStep");
        ProcessStepBuilder repeatEchoStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>("repeatEchoStep");
        ProcessStepBuilder echoStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>("echoStep");
        ProcessStepBuilder emitterStep = processBuilder.AddStepFromType<EmitterStep>("emitterStep");
        ProcessStepBuilder fanInStep = processBuilder.AddStepFromType<FanInStep>("fanInStep");

        processBuilder
            .OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        repeatStep
            .OnEvent(ProcessTestsEvents.OutputReadyInternal)
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatEchoStep));

        processBuilder.ListenFor().AllOf(
            [
                new(ProcessTestsEvents.StartProcess, processBuilder),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(emitterStep, functionName: EmitterStep.DualInputPublicEventFunction, inputMapping: inputEvents =>
            {
                return new()
                {
                    { "firstInput", inputEvents[processBuilder.GetFullEventId(ProcessTestsEvents.StartProcess)]  },
                    { "secondInput", inputEvents[processBuilder.GetFullEventId(ProcessTestsEvents.StartProcess)] }
                };
            }));

        processBuilder.ListenFor().AllOf(
            [
                new(ProcessTestsEvents.OutputReadyInternal, repeatStep),
                new(echoStep.GetFunctionResultEventId(), echoStep)
            ])
            .SendEventTo(new ProcessStepTargetBuilder(emitterStep, functionName: EmitterStep.QuadInputPublicEventFunction, inputMapping: inputEvents =>
            {
                return new()
                {
                    { "firstInput", inputEvents[repeatStep.GetFullEventId(ProcessTestsEvents.OutputReadyInternal)] },
                    { "secondInput", inputEvents[echoStep.GetFullEventId()] },
                    { "fourthInput", "someFixedInputFromProcessDefinition" },
                };
            }));

        processBuilder.ListenFor().AllOf(
            [
                new(ProcessTestsEvents.OutputReadyPublic, emitterStep),
                new(ProcessTestsEvents.OutputReadySecondaryPublic, emitterStep),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(fanInStep, inputMapping: inputEvents =>
            {
                return new()
                {
                    { "firstInput", inputEvents[emitterStep.GetFullEventId(ProcessTestsEvents.OutputReadyPublic)] },
                    { "secondInput", inputEvents[emitterStep.GetFullEventId(ProcessTestsEvents.OutputReadySecondaryPublic)] }
                };
            }));

        return processBuilder;
    }

    /// <summary>
    /// Sample process with a fan in step that takes the output of two steps from same step and combines them.<br/>
    /// Fan in step - emitter - has multiple functions and some have multiple parameters.<br/>
    /// This test is meant to test the ability to create multiple internal edgeGroups in the same step.<br/>
    /// <code>
    /// ┌────────┐
    /// │ repeat ├───┐
    /// └────────┘   │ ┌────────┐  ┌─────────┐     ┌─────────┐
    ///              └►│ r_echo ├─►│         ├────►│         │
    ///                └────────┘  │ emitter │     │  fanIn  │
    ///              ┌-───────────►│         ├────►│         │
    /// ┌────────┐   │             └─────────┘     └─────────┘
    /// │  echo  ├───┘
    /// └────────┘
    /// </code>
    /// </summary>
    /// <param name="name"></param>
    /// <returns></returns>
    private ProcessBuilder CreateProcessWithFanInUsingStepWithMultipleFunctionsAndParametersSimultaneouslyFromStepsOnly(string name)
    {
        ProcessBuilder processBuilder = new(name);
        ProcessStepBuilder repeatStep = processBuilder.AddStepFromType<RepeatStep>("repeatStep");
        ProcessStepBuilder repeatEchoStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>("repeatEchoStep");
        ProcessStepBuilder echoStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>("echoStep");
        ProcessStepBuilder emitterStep = processBuilder.AddStepFromType<EmitterStep>("emitterStep");
        ProcessStepBuilder fanInStep = processBuilder.AddStepFromType<FanInStep>("fanInStep");

        processBuilder
            .OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        repeatStep
            .OnEvent(ProcessTestsEvents.OutputReadyInternal)
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatEchoStep));

        processBuilder.ListenFor().AllOf(
            [
                new(ProcessTestsEvents.StartProcess, processBuilder),
                new(repeatEchoStep.GetFunctionResultEventId(), repeatEchoStep),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(emitterStep, functionName: EmitterStep.DualInputPublicEventFunction, inputMapping: inputEvents =>
            {
                return new()
                {
                    { "firstInput", inputEvents[repeatEchoStep.GetFullEventId()] },
                    { "secondInput", inputEvents[processBuilder.GetFullEventId(ProcessTestsEvents.StartProcess)] }
                };
            }));

        processBuilder.ListenFor().AllOf(
            [
                new(ProcessTestsEvents.OutputReadyInternal, repeatStep),
                new(echoStep.GetFunctionResultEventId(), echoStep)
            ])
            .SendEventTo(new ProcessStepTargetBuilder(emitterStep, functionName: EmitterStep.QuadInputPublicEventFunction, inputMapping: inputEvents =>
            {
                return new()
                {
                    { "firstInput", inputEvents[repeatStep.GetFullEventId(ProcessTestsEvents.OutputReadyInternal)] },
                    { "secondInput", inputEvents[echoStep.GetFullEventId()] },
                    { "fourthInput", "someFixedInputFromProcessDefinition" },
                };
            }));

        processBuilder.ListenFor().AllOf(
            [
                new(ProcessTestsEvents.OutputReadyPublic, emitterStep),
                new(ProcessTestsEvents.OutputReadySecondaryPublic, emitterStep),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(fanInStep, inputMapping: inputEvents =>
            {
                return new()
                {
                    { "firstInput", inputEvents[emitterStep.GetFullEventId(ProcessTestsEvents.OutputReadyPublic)] },
                    { "secondInput", inputEvents[emitterStep.GetFullEventId(ProcessTestsEvents.OutputReadySecondaryPublic)] }
                };
            }));

        return processBuilder;
    }

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

        processBuilder.ListenFor().AllOf(
            [
                new(EmitterStep.EventId, firstNestedStep),
                new(EmitterStep.EventId, ninthNestedStep),
            ])
            .SendEventTo(new ProcessStepTargetBuilder(tenthNestedStep, functionName: EmitterStep.DualInputPublicEventFunction, inputMapping: (inputEvents) =>
            {
                // Map the input events to the parameters of the tenth step.
                return new()
                {
                    { "firstInput", inputEvents[firstNestedStep.GetFullEventId(EmitterStep.EventId)] },
                    { "secondInput", inputEvents[ninthNestedStep.GetFullEventId(EmitterStep.EventId)] }
                };
            }));

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
        var echoStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>(id: nameof(CommonSteps.EchoStep));
        var repeatStep = processBuilder.AddStepFromType<RepeatStep>(id: nameof(RepeatStep));

        processBuilder
            .OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        echoStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatStep));

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
        var fanInCStep = processBuilder.AddStepFromType<FanInStep>(id: nameof(FanInStep));

        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess).SendEventTo(new ProcessFunctionTargetBuilder(echoAStep));
        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess).SendEventTo(new ProcessFunctionTargetBuilder(repeatBStep));

        processBuilder.ListenFor().AllOf(
            [
                new(echoAStep.GetFunctionResultEventId(), echoAStep),
                new(ProcessTestsEvents.OutputReadyPublic, repeatBStep)
            ])
            .SendEventTo(new ProcessStepTargetBuilder(fanInCStep, inputMapping: (inputEvents) =>
            {
                // Map the input events to the parameters of the fan-in step.
                return new()
                {
                    { "firstInput", inputEvents[echoAStep.GetFullEventId(echoAStep.GetFunctionResultEventId())] },
                    { "secondInput", inputEvents[repeatBStep.GetFullEventId(ProcessTestsEvents.OutputReadyPublic)] }
                };
            }));

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
        errorStep.OnEvent(ProcessTestsEvents.ErrorStepSuccess).SendEventTo(new ProcessFunctionTargetBuilder(repeatStep));
        errorStep.OnFunctionError("ErrorWhenTrue").SendEventTo(new ProcessFunctionTargetBuilder(reportStep));

        return processBuilder;
    }
    #endregion

    #region Assert Utils
    private void AssertStepStateLastMessage(KernelProcess processInfo, string stepName, string? expectedLastMessage, int? expectedInvocationCount = null)
    {
        KernelProcessStepInfo? stepInfo = processInfo.Steps.FirstOrDefault(s => s.State.StepId == stepName);
        Assert.NotNull(stepInfo);
        var outputStepResult = stepInfo.State as KernelProcessStepState<StepState>;
        Assert.NotNull(outputStepResult?.State);
        Assert.Equal(expectedLastMessage, outputStepResult.State.LastMessage);
        if (expectedInvocationCount.HasValue)
        {
            Assert.Equal(expectedInvocationCount.Value, outputStepResult.State.InvocationCount);
        }
    }
    private void AssertStepState<T>(KernelProcess processInfo, string stepName, Func<KernelProcessStepState<T>, bool> predicate) where T : class, new()
    {
        KernelProcessStepInfo? stepInfo = processInfo.Steps.FirstOrDefault(s => s.State.StepId == stepName);
        Assert.NotNull(stepInfo);
        var outputStepResult = stepInfo.State as KernelProcessStepState<T>;
        Assert.NotNull(outputStepResult?.State);
        Assert.True(predicate(outputStepResult));
    }
    #endregion
}
