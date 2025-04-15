// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.Serialization;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using SemanticKernel.Process.TestsShared.CloudEvents;
using SemanticKernel.Process.TestsShared.Steps;
using Xunit;
#pragma warning restore IDE0005 // Using directive is unnecessary.

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Integration tests for processes.
/// </summary>
[Collection(nameof(ProcessTestGroup))]
public sealed class ProcessCloudEventsTests : IClassFixture<ProcessTestFixture>
{
    private readonly ProcessTestFixture _fixture;
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIConfiguration>()
            .Build();

    private readonly string _topic1 = "myTopic1";
    private readonly string _topic2 = "MyTopic2";

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessTests"/> class. This is called by the test framework.
    /// </summary>
    /// <param name="fixture"></param>
    public ProcessCloudEventsTests(ProcessTestFixture fixture)
    {
        this._fixture = fixture;
    }

    /// <summary>
    /// Tests that evaluates basic behavior of process using "EmitExternalEvent" in the processBuilder
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task LinearProcessWithCloudEventSubscribersUsingEmitToTopicAsync()
    {
        // Arrange
        MockCloudEventClient.Instance.Reset();
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();
        var process = this.CreateLinearProcessWithEmitTopic("SimpleWithCloudEvents").Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput }, MockCloudEventClient.Instance);
        var externalMessageChannel = await processHandle.GetExternalMessageChannelAsync();
        var runningProcessId = await processHandle.GetProcessIdAsync();

        // Assert
        Assert.NotNull(externalMessageChannel);
        var mockClient = (MockCloudEventClient)externalMessageChannel;
        Assert.NotNull(mockClient);
        Assert.True(mockClient.InitializationCounter > 0);
        Assert.Equal(2, mockClient.CloudEvents.Count);
        Assert.Equal(runningProcessId, mockClient.CloudEvents[0].ProcessId);
        Assert.Equal(runningProcessId, mockClient.CloudEvents[1].ProcessId);
        this.AssertProxyMessage(mockClient.CloudEvents[0], expectedPublishTopic: MockTopicNames.EchoExternalTopic, expectedTopicData: testInput);
        this.AssertProxyMessage(mockClient.CloudEvents[1], expectedPublishTopic: MockTopicNames.RepeatExternalTopic, expectedTopicData: $"{testInput} {testInput}");
    }

    /// <summary>
    /// Validates the proxy used in subprocesses act as expected with different external topics
    /// </summary>
    [Fact]
    public async Task ProcessWithSubprocessWithProxyEmittingDifferentTopicsAsync()
    {
        // Arrange
        MockCloudEventClient.Instance.Reset();
        ProcessBuilder processBuilder = new(nameof(ProcessWithSubprocessWithProxyEmittingDifferentTopicsAsync));

        var subprocess1 = processBuilder.AddStepFromProcess(this.CreateSimpleEchoProcess("subprocess1", this._topic1));
        var subprocess2 = processBuilder.AddStepFromProcess(this.CreateSimpleEchoProcess("subprocess2", this._topic2));

        processBuilder
            .OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(subprocess1.WhereInputEventIs(ProcessTestsEvents.StartInnerProcess))
            .SendEventTo(subprocess2.WhereInputEventIs(ProcessTestsEvents.StartInnerProcess));

        KernelProcess process = processBuilder.Build();
        Kernel kernel = new();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput }, MockCloudEventClient.Instance);
        var externalMessageChannel = await processHandle.GetExternalMessageChannelAsync();

        // Assert
        Assert.NotNull(externalMessageChannel);
        var mockClient = (MockCloudEventClient)externalMessageChannel;
        Assert.NotNull(mockClient);
        Assert.True(mockClient.InitializationCounter > 0);
        Assert.Equal(2, mockClient.CloudEvents.Count);
        if (mockClient.CloudEvents[0].ExternalTopicName == this._topic1)
        {
            this.AssertProxyMessage(mockClient.CloudEvents[0], expectedPublishTopic: this._topic1, expectedTopicData: testInput);
            this.AssertProxyMessage(mockClient.CloudEvents[1], expectedPublishTopic: this._topic2, expectedTopicData: testInput);
        }
        else
        {
            this.AssertProxyMessage(mockClient.CloudEvents[0], expectedPublishTopic: this._topic2, expectedTopicData: testInput);
            this.AssertProxyMessage(mockClient.CloudEvents[1], expectedPublishTopic: this._topic1, expectedTopicData: testInput);
        }
    }

    /// <summary>
    /// Validates the proxy used in subprocesses act as expected with same external topics
    /// </summary>
    [Fact]
    public async Task ProcessWithSubprocessWithProxyEmittingSameTopicsAsync()
    {
        // Arrange
        MockCloudEventClient.Instance.Reset();
        ProcessBuilder processBuilder = new(nameof(ProcessWithSubprocessWithProxyEmittingSameTopicsAsync));

        var subprocess1 = processBuilder.AddStepFromProcess(this.CreateSimpleEchoProcess("subprocess1", this._topic1));
        var subprocess2 = processBuilder.AddStepFromProcess(this.CreateSimpleEchoProcess("subprocess2", this._topic1));

        processBuilder
            .OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(subprocess1.WhereInputEventIs(ProcessTestsEvents.StartInnerProcess))
            .SendEventTo(subprocess2.WhereInputEventIs(ProcessTestsEvents.StartInnerProcess));

        KernelProcess process = processBuilder.Build();
        Kernel kernel = new();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput }, MockCloudEventClient.Instance);
        var externalMessageChannel = await processHandle.GetExternalMessageChannelAsync();

        // Assert
        Assert.NotNull(externalMessageChannel);
        var mockClient = (MockCloudEventClient)externalMessageChannel;
        Assert.NotNull(mockClient);
        Assert.True(mockClient.InitializationCounter > 0);
        Assert.Equal(2, mockClient.CloudEvents.Count);
        this.AssertProxyMessage(mockClient.CloudEvents[0], expectedPublishTopic: this._topic1, expectedTopicData: testInput);
        this.AssertProxyMessage(mockClient.CloudEvents[1], expectedPublishTopic: this._topic1, expectedTopicData: testInput);
    }

    /// <summary>
    /// Creates a simple linear process with two steps and a proxy step to emit events externally<br/>
    /// Input Event: <see cref="ProcessTestsEvents.StartProcess"/><br/>
    /// Output Events: [<see cref="ProcessTestsEvents.OutputReadyInternal"/>, <see cref="ProcessTestsEvents.OutputReadyPublic"/>]<br/>
    /// <code>
    /// ┌────────┐    ┌────────┐
    /// │  echo  ├───►│ repeat ├───►
    /// └────────┘ │  └────────┘ │
    ///
    ///            │  ┌───────┐  │
    ///            └─►│ proxy │◄─┘
    ///               └───────┘
    /// </code>
    /// </summary>
    private ProcessBuilder CreateLinearProcessWithEmitTopic(string name)
    {
        var processBuilder = new ProcessBuilder(name);
        var echoStep = processBuilder.AddStepFromType<CommonSteps.EchoStep>();
        var repeatStep = processBuilder.AddStepFromType<RepeatStep>();

        var proxyTopics = new List<string>() { MockTopicNames.RepeatExternalTopic, MockTopicNames.EchoExternalTopic };
        var proxyStep = processBuilder.AddProxyStep(proxyTopics);

        processBuilder
            .OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        echoStep
            .OnFunctionResult(nameof(CommonSteps.EchoStep.Echo))
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatStep, parameterName: "message"));

        echoStep
            .OnFunctionResult()
            .EmitExternalEvent(proxyStep, MockTopicNames.EchoExternalTopic);

        repeatStep
            .OnEvent(ProcessTestsEvents.OutputReadyInternal)
            .EmitExternalEvent(proxyStep, MockTopicNames.RepeatExternalTopic);

        return processBuilder;
    }

    private ProcessBuilder CreateSimpleEchoProcess(string processName, string proxyTopicName)
    {
        ProcessBuilder process = new(processName);

        var echoStep = process.AddStepFromType<CommonSteps.EchoStep>();
        var proxyStep = process.AddProxyStep([this._topic1, this._topic2]);

        process
            .OnInputEvent(ProcessTestsEvents.StartInnerProcess)
            .SendEventTo(new(echoStep));

        echoStep
            .OnFunctionResult()
            .EmitExternalEvent(proxyStep, proxyTopicName);

        return process;
    }

    #region Assert Utils
    private void AssertProxyMessage(KernelProcessProxyMessage? proxyMessage, string expectedPublishTopic, object? expectedTopicData = null)
    {
        Assert.NotNull(proxyMessage);
        Assert.IsType<KernelProcessProxyMessage>(proxyMessage);
        Assert.Equal(expectedPublishTopic, proxyMessage.ExternalTopicName);

        Assert.IsType<KernelProcessEventData>(proxyMessage.EventData);
        var outputEventData = proxyMessage.EventData.ToObject();
        Assert.IsType<string>(outputEventData);
        Assert.Equal(expectedTopicData, outputEventData);
    }
    #endregion
}
