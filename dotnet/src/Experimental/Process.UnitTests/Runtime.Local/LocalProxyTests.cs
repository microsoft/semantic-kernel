// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;
using SemanticKernel.Process.TestsShared.CloudEvents;
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
    private readonly string _topic3 = "my_topic_3";

    private readonly string _startProcessEvent = "startProcess";

    /// <summary>
    /// Validates the <see cref="LocalProxy"/> result as the first step in the process
    /// and with a step as the map operation.
    /// </summary>
    [Fact]
    public async Task ProcessWithProxyWithSingleTopicCalledTwiceAsync()
    {
        // Arrange
        var mockProxyClient = MockCloudEventClient.Instance;
        ProcessBuilder process = new(nameof(ProcessWithProxyWithSingleTopicCalledTwiceAsync));

        var counterStep = process.AddStepFromType<CommonSteps.CountStep>();
        var proxyStep = process.AddProxyStep<MockCloudEventClient>([this._topic1, this._topic2, this._topic3]);

        process.OnInputEvent(this._startProcessEvent).SendEventTo(new(counterStep));
        counterStep.OnFunctionResult().EmitExternalEvent(proxyStep, this._topic1);

        KernelProcess processInstance = process.Build();
        Kernel kernel = new();

        // Act
        LocalKernelProcessContext processContext = await this.RunProcessAsync(kernel, processInstance, null, this._startProcessEvent, externalMessageChannel: mockProxyClient);

        // Assert
        Assert.NotNull(mockProxyClient);
        Assert.Equal(1, mockProxyClient.InitializationCounter);
        Assert.Single(mockProxyClient.CloudEvents);
        Assert.Equal(this._topic1, mockProxyClient.CloudEvents[0].TopicName);
        Assert.Equal("1", mockProxyClient.CloudEvents[0].Data?.EventData);

        // Act
        await processContext.SendEventAsync(new() { Id = this._startProcessEvent, Data = null });

        // Assert
        Assert.NotNull(mockProxyClient);
        Assert.Equal(1, mockProxyClient.InitializationCounter);
        Assert.Equal(2, mockProxyClient.CloudEvents.Count);
        Assert.Equal(this._topic1, mockProxyClient.CloudEvents[1].TopicName);
        Assert.Equal("2", mockProxyClient.CloudEvents[1].Data?.EventData);
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
