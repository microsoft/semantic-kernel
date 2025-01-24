// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary.
using System;
using System.Linq;
using System.Runtime.Serialization;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using SemanticKernel.Process.IntegrationTests.CloudEvents;
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

    private readonly IExternalKernelProcessMessageChannel _externalMessageChannel = MockCloudEventClient.Instance;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessTests"/> class. This is called by the test framework.
    /// </summary>
    /// <param name="fixture"></param>
    public ProcessCloudEventsTests(ProcessTestFixture fixture)
    {
        this._fixture = fixture;
    }

    /// <summary>
    /// Tests a simple linear process with two steps and no sub processes.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task LinearProcessWithCloudEventSubscribersAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        this._kernelBuilder.AddOpenAIChatCompletion(
            modelId: configuration.ModelId!,
            apiKey: configuration.ApiKey);

        Kernel kernel = this._kernelBuilder.Build();
        var process = this.CreateLinearProcess("SimpleWithCloudEvents").Build();

        // Act
        string testInput = "Test";
        var processHandle = await this._fixture.StartProcessAsync(process, kernel, new() { Id = ProcessTestsEvents.StartProcess, Data = testInput }, this._externalMessageChannel);
        var externalMessageChannel = await processHandle.GetExternalMessageChannelAsync();

        // Assert
        Assert.NotNull(externalMessageChannel);
        var mockClient = (MockCloudEventClient)externalMessageChannel;
        Assert.NotNull(mockClient);
        Assert.True(mockClient.InitializationCounter > 0);
        Assert.Equal(2, mockClient.CloudEvents.Count);
        Assert.Equal(testInput, mockClient.CloudEvents[0].Data);
        Assert.Equal(MockProxyStep.TopicNames.EchoExternalTopic, mockClient.CloudEvents[0].TopicName);
        Assert.Equal($"{testInput} {testInput}", mockClient.CloudEvents[1].Data);
        Assert.Equal(MockProxyStep.TopicNames.RepeatExternalTopic, mockClient.CloudEvents[1].TopicName);
    }

    /// <summary>
    /// Creates a simple linear process with two steps and a proxy step to emit events externally<br/>
    /// Input Event: <see cref="ProcessTestsEvents.StartProcess"/><br/>
    /// Output Events: [<see cref="ProcessTestsEvents.OutputReadyInternal"/>, <see cref="ProcessTestsEvents.OutputReadyPublic"/>]<br/>
    /// <code>
    /// ┌────────┐    ┌────────┐
    /// │  echo  ├─┬─►│ repeat ├───┐
    /// └────────┘ │  └────────┘   │
    ///            │               │
    ///            │  ┌───────┐    │
    ///            └─►│ proxy │◄───┘
    ///               └───────┘
    /// </code>
    /// </summary>
    private ProcessBuilder CreateLinearProcess(string name)
    {
        var processBuilder = new ProcessBuilder(name);
        var echoStep = processBuilder.AddStepFromType<EchoStep>();
        var repeatStep = processBuilder.AddStepFromType<RepeatStep>();
        var proxyStep = processBuilder.AddStepFromType<MockProxyStep>();

        processBuilder.OnInputEvent(ProcessTestsEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(echoStep));

        echoStep.OnFunctionResult(nameof(EchoStep.Echo))
            .SendEventTo(new ProcessFunctionTargetBuilder(repeatStep, parameterName: "message"));

        echoStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(proxyStep, functionName: MockProxyStep.FunctionNames.OnEchoMessage));

        repeatStep
            .OnEvent(ProcessTestsEvents.OutputReadyInternal)
            .SendEventTo(new ProcessFunctionTargetBuilder(proxyStep, functionName: MockProxyStep.FunctionNames.OnRepeatMessage));

        return processBuilder;
    }
}
