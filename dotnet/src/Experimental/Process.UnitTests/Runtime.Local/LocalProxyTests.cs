// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading.Tasks;
using SemanticKernel.Process.TestsShared.CloudEvents;
using SemanticKernel.Process.TestsShared.Services;
using SemanticKernel.Process.TestsShared.Setup;
using SemanticKernel.Process.TestsShared.Steps;
using Xunit;

namespace Microsoft.SemanticKernel.Process.Runtime.Local.UnitTests;

/// <summary>
/// Unit tests for the <see cref="LocalProxy"/> class.
/// </summary>
public class LocalProxyTests
{
    private readonly string _topic1 = "myTopic1";
    private readonly string _topic2 = "MyTopic2";

    private readonly string _startProcessEvent = "startProcess";

    /// <summary>
    /// Validates the <see cref="LocalProxy"/> result called once and then after process stops
    /// </summary>
    [Fact]
    public async Task ProcessWithProxyWithSingleTopicCalledTwiceAsync()
    {
        // Arrange
        var mockProxyClient = new MockCloudEventClient();
        ProcessBuilder process = new(nameof(ProcessWithProxyWithSingleTopicCalledTwiceAsync));

        var counterStep = process.AddStepFromType<CommonSteps.CountStep>(name: nameof(ProcessWithProxyWithSingleTopicCalledTwiceAsync));
        var proxyStep = process.AddProxyStep([this._topic1, this._topic2]);

        process.OnInputEvent(this._startProcessEvent).SendEventTo(new(counterStep));
        counterStep.OnFunctionResult().EmitExternalEvent(proxyStep, this._topic1);

        KernelProcess processInstance = process.Build();
        CounterService counterService = new();
        Kernel kernel = KernelSetup.SetupKernelWithCounterService(counterService);

        // Act
        await using (LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, null, this._startProcessEvent, externalMessageChannel: mockProxyClient))
        {
            // Assert
            var runningProcessId = await processContext.GetProcessIdAsync();

            Assert.NotNull(mockProxyClient);
            Assert.Equal(1, mockProxyClient.InitializationCounter);
            Assert.Equal(0, mockProxyClient.UninitializationCounter);
            Assert.Single(mockProxyClient.CloudEvents);
            Assert.Equal(this._topic1, mockProxyClient.CloudEvents[0].ExternalTopicName);
            Assert.Equal(runningProcessId, mockProxyClient.CloudEvents[0].ProcessId);
            Assert.Equal("1", mockProxyClient.CloudEvents[0].EventData?.ToObject());

            // Act
            await processContext.SendEventAsync(new() { Id = this._startProcessEvent, Data = null });

            // Assert
            Assert.NotNull(mockProxyClient);
            Assert.Equal(1, mockProxyClient.InitializationCounter);
            Assert.Equal(0, mockProxyClient.UninitializationCounter);
            Assert.Equal(2, mockProxyClient.CloudEvents.Count);
            Assert.Equal(this._topic1, mockProxyClient.CloudEvents[1].ExternalTopicName);
            Assert.Equal(runningProcessId, mockProxyClient.CloudEvents[0].ProcessId);
            Assert.Equal("2", mockProxyClient.CloudEvents[1].EventData?.ToObject());
        }
        Assert.Equal(1, mockProxyClient.UninitializationCounter);
    }

    /// <summary>
    /// Validates the <see cref="LocalProxy"/> fails when using unregistered topic
    /// </summary>
    [Fact]
    public void ProcessWithProxyFailsToCreateDueMissingTopicRegistration()
    {
        // Arrange
        var mockProxyClient = new MockCloudEventClient();
        ProcessBuilder process = new(nameof(ProcessWithProxyFailsToCreateDueMissingTopicRegistration));

        var counterStep = process.AddStepFromType<CommonSteps.CountStep>(name: nameof(ProcessWithProxyFailsToCreateDueMissingTopicRegistration));
        var proxyStep = process.AddProxyStep([this._topic1]);

        process.OnInputEvent(this._startProcessEvent).SendEventTo(new(counterStep));

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => counterStep.OnFunctionResult().EmitExternalEvent(proxyStep, this._topic2));
    }

    /// <summary>
    /// Validates the <see cref="LocalProxy"/> emits different topics from
    /// different steps
    /// </summary>
    [Fact]
    public async Task ProcessWithCyclesAndProxyWithTwoTopicsAsync()
    {
        // Arrange
        var mockProxyClient = new MockCloudEventClient();
        ProcessBuilder process = this.GetSampleProcessWithProxyEmittingTwoTopics(nameof(ProcessWithCyclesAndProxyWithTwoTopicsAsync), counterName: nameof(ProcessWithCyclesAndProxyWithTwoTopicsAsync));
        KernelProcess processInstance = process.Build();
        CounterService counterService = new();
        Kernel kernel = KernelSetup.SetupKernelWithCounterService(counterService);

        // Act
        await using (LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, null, this._startProcessEvent, externalMessageChannel: mockProxyClient))
        {
            // Assert
            var runningProcessId = await processContext.GetProcessIdAsync();

            Assert.NotNull(mockProxyClient);
            Assert.True(0 < mockProxyClient.InitializationCounter);
            Assert.Equal(0, mockProxyClient.UninitializationCounter);
            Assert.Equal(3, mockProxyClient.CloudEvents.Count);
            Assert.Equal(this._topic1, mockProxyClient.CloudEvents[0].ExternalTopicName);
            Assert.Equal(runningProcessId, mockProxyClient.CloudEvents[0].ProcessId);
            Assert.Equal("1", mockProxyClient.CloudEvents[0].EventData?.ToObject());
            Assert.Equal(this._topic1, mockProxyClient.CloudEvents[1].ExternalTopicName);
            Assert.Equal("2", mockProxyClient.CloudEvents[1].EventData?.ToObject());
            Assert.Equal(this._topic2, mockProxyClient.CloudEvents[2].ExternalTopicName);
            Assert.Equal("2", mockProxyClient.CloudEvents[2].EventData?.ToObject());
        }

        // Assert
        Assert.Equal(1, mockProxyClient.UninitializationCounter);
    }

    /// <summary>
    /// Validates the <see cref="LocalProxy"/> emits different topics from
    /// different steps from a nested process
    /// </summary>
    [Fact]
    public async Task ProcessWithProxyIn2LevelsNestedProcessEmitsTwoTopicsAsync()
    {
        // Arrange
        var mockProxyClient = new MockCloudEventClient();
        ProcessBuilder process = new(nameof(ProcessWithProxyIn2LevelsNestedProcessEmitsTwoTopicsAsync));
        var innerProcess = process.AddStepFromProcess(this.GetSampleProcessWithProxyEmittingTwoTopics(
            $"Inner-{nameof(ProcessWithProxyIn2LevelsNestedProcessEmitsTwoTopicsAsync)}", counterName: nameof(ProcessWithProxyIn2LevelsNestedProcessEmitsTwoTopicsAsync)));

        process
            .OnInputEvent(this._startProcessEvent)
            .SendEventTo(innerProcess.WhereInputEventIs(this._startProcessEvent));

        KernelProcess processInstance = process.Build();
        CounterService counterService = new();
        Kernel kernel = KernelSetup.SetupKernelWithCounterService(counterService);

        // Act
        await using (LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, null, this._startProcessEvent, externalMessageChannel: mockProxyClient))
        {
            // Assert
            var runningProcessId = await processContext.GetProcessIdAsync();

            Assert.NotNull(mockProxyClient);
            Assert.True(0 < mockProxyClient.InitializationCounter);
            Assert.Equal(0, mockProxyClient.UninitializationCounter);
            Assert.Equal(3, mockProxyClient.CloudEvents.Count);
            Assert.Equal(this._topic1, mockProxyClient.CloudEvents[0].ExternalTopicName);
            Assert.Equal(runningProcessId, mockProxyClient.CloudEvents[0].ProcessId);
            Assert.Equal("1", mockProxyClient.CloudEvents[0].EventData?.ToObject());
            Assert.Equal(this._topic1, mockProxyClient.CloudEvents[1].ExternalTopicName);
            Assert.Equal("2", mockProxyClient.CloudEvents[1].EventData?.ToObject());
            Assert.Equal(this._topic2, mockProxyClient.CloudEvents[2].ExternalTopicName);
            Assert.Equal("2", mockProxyClient.CloudEvents[2].EventData?.ToObject());
        }

        // Assert
        Assert.Equal(1, mockProxyClient.UninitializationCounter);
    }

    /// <summary>
    /// Validates the <see cref="LocalProxy"/> emits different topics from
    /// different steps from a deep nested process
    /// </summary>
    [Fact]
    public async Task ProcessWithProxyIn4LevelsNestedProcessEmitsTwoTopicsAsync()
    {
        // Arrange
        var mockProxyClient = new MockCloudEventClient();
        ProcessBuilder process = new(nameof(ProcessWithProxyIn4LevelsNestedProcessEmitsTwoTopicsAsync));
        var innerProcess = process.AddStepFromProcess(
            this.GetNestedProcess(
                processName: $"Inner1-{nameof(ProcessWithProxyIn4LevelsNestedProcessEmitsTwoTopicsAsync)}",
                internalProcess: this.GetSampleProcessWithProxyEmittingTwoTopics(
                    $"Inner2-{nameof(ProcessWithProxyIn4LevelsNestedProcessEmitsTwoTopicsAsync)}",
                    $"Inner2_{nameof(ProcessWithProxyIn4LevelsNestedProcessEmitsTwoTopicsAsync)}"),
                inputEventName: this._startProcessEvent,
                counterName: $"Inner1_{nameof(ProcessWithProxyIn4LevelsNestedProcessEmitsTwoTopicsAsync)}"));

        process
            .OnInputEvent(this._startProcessEvent)
            .SendEventTo(innerProcess.WhereInputEventIs(this._startProcessEvent));

        KernelProcess processInstance = process.Build();
        CounterService counterService = new();
        Kernel kernel = KernelSetup.SetupKernelWithCounterService(counterService);

        // Act
        await using (LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, null, this._startProcessEvent, externalMessageChannel: mockProxyClient))
        {
            // Assert
            var runningProcessId = await processContext.GetProcessIdAsync();

            Assert.NotNull(mockProxyClient);
            Assert.True(0 < mockProxyClient.InitializationCounter);
            Assert.Equal(0, mockProxyClient.UninitializationCounter);
            Assert.Equal(3, mockProxyClient.CloudEvents.Count);
            Assert.Equal(this._topic1, mockProxyClient.CloudEvents[0].ExternalTopicName);
            Assert.Equal(runningProcessId, mockProxyClient.CloudEvents[0].ProcessId);
            Assert.Equal("1", mockProxyClient.CloudEvents[0].EventData?.ToObject());
            Assert.Equal(this._topic1, mockProxyClient.CloudEvents[1].ExternalTopicName);
            Assert.Equal("2", mockProxyClient.CloudEvents[1].EventData?.ToObject());
            Assert.Equal(this._topic2, mockProxyClient.CloudEvents[2].ExternalTopicName);
            Assert.Equal("2", mockProxyClient.CloudEvents[2].EventData?.ToObject());
        }

        // Assert
        Assert.Equal(1, mockProxyClient.UninitializationCounter);
    }

    private ProcessBuilder GetNestedProcess(string processName, ProcessBuilder internalProcess, string inputEventName, string counterName)
    {
        ProcessBuilder process = new(processName);
        var innerProcess = process.AddStepFromProcess(this.GetSampleProcessWithProxyEmittingTwoTopics($"Inner-{processName}", counterName));

        process
            .OnInputEvent(inputEventName)
            .SendEventTo(innerProcess.WhereInputEventIs(inputEventName));

        return process;
    }

    private ProcessBuilder GetSampleProcessWithProxyEmittingTwoTopics(string processName, string counterName)
    {
        ProcessBuilder process = new(processName);

        var counterStep = process.AddStepFromType<CommonSteps.CountStep>(name: counterName);
        var evenNumberStep = process.AddStepFromType<CommonSteps.EvenNumberDetectorStep>();
        var proxyStep = process.AddProxyStep([this._topic1, this._topic2]);

        process
            .OnInputEvent(this._startProcessEvent)
            .SendEventTo(new(counterStep));

        counterStep
            .OnFunctionResult()
            .EmitExternalEvent(proxyStep, this._topic1)
            .SendEventTo(new(evenNumberStep));

        // request another number if number is odd
        evenNumberStep
            .OnEvent(CommonSteps.EvenNumberDetectorStep.OutputEvents.OddNumber)
            .SendEventTo(new(counterStep));

        evenNumberStep
            .OnEvent(CommonSteps.EvenNumberDetectorStep.OutputEvents.EvenNumber)
            .EmitExternalEvent(proxyStep, this._topic2);

        return process;
    }

    private async Task<LocalKernelProcessContext> RunProcessAsync(Kernel kernel, KernelProcess process, object? input, string inputEvent, IExternalKernelProcessMessageChannel? externalMessageChannel)
    {
        return
            await process.StartAsync(
                kernel,
                new KernelProcessEvent
                {
                    Id = inputEvent,
                    Data = input,
                },
                externalMessageChannel);
    }
}
