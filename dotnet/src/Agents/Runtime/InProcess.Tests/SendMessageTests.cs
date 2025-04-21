// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;
using FluentAssertions;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.InProcess.Tests;

[Trait("Category", "Unit")]
public class SendMessageTests
{
    [Fact]
    public async Task Test_SendMessage_ReturnsValue()
    {
        static string ProcessFunc(string s) => $"Processed({s})";

        MessagingTestFixture fixture = new();

        await fixture.RegisterFactoryMapInstances(nameof(ProcessorAgent),
            (id, runtime) => ValueTask.FromResult(new ProcessorAgent(id, runtime, ProcessFunc, string.Empty)));

        AgentId targetAgent = new(nameof(ProcessorAgent), Guid.NewGuid().ToString());
        object? maybeResult = await fixture.RunSendTestAsync(targetAgent, new BasicMessage { Content = "1" });

        maybeResult.Should().NotBeNull()
            .And.BeOfType<BasicMessage>()
            .And.Match<BasicMessage>(m => m.Content == "Processed(1)");
    }

    [Fact]
    public async Task Test_SendMessage_Cancellation()
    {
        MessagingTestFixture fixture = new();

        await fixture.RegisterFactoryMapInstances(nameof(CancelAgent),
            (id, runtime) => ValueTask.FromResult(new CancelAgent(id, runtime, string.Empty)));

        AgentId targetAgent = new(nameof(CancelAgent), Guid.NewGuid().ToString());
        Func<Task> testAction = () => fixture.RunSendTestAsync(targetAgent, new BasicMessage { Content = "1" }).AsTask();

        await testAction.Should().ThrowAsync<OperationCanceledException>();
    }

    [Fact]
    public async Task Test_SendMessage_Error()
    {
        MessagingTestFixture fixture = new();

        await fixture.RegisterFactoryMapInstances(nameof(ErrorAgent),
            (id, runtime) => ValueTask.FromResult(new ErrorAgent(id, runtime, string.Empty)));

        AgentId targetAgent = new(nameof(ErrorAgent), Guid.NewGuid().ToString());
        Func<Task> testAction = () => fixture.RunSendTestAsync(targetAgent, new BasicMessage { Content = "1" }).AsTask();

        await testAction.Should().ThrowAsync<TestException>();
    }

    [Fact]
    public async Task Test_SendMessage_FromSendMessageHandler()
    {
        Guid[] targetGuids = [Guid.NewGuid(), Guid.NewGuid()];

        MessagingTestFixture fixture = new();

        Dictionary<AgentId, SendOnAgent> sendAgents = fixture.GetAgentInstances<SendOnAgent>();
        Dictionary<AgentId, ReceiverAgent> receiverAgents = fixture.GetAgentInstances<ReceiverAgent>();

        await fixture.RegisterFactoryMapInstances(nameof(SendOnAgent),
            (id, runtime) => ValueTask.FromResult(new SendOnAgent(id, runtime, string.Empty, targetGuids)));

        await fixture.RegisterFactoryMapInstances(nameof(ReceiverAgent),
            (id, runtime) => ValueTask.FromResult(new ReceiverAgent(id, runtime, string.Empty)));

        AgentId targetAgent = new(nameof(SendOnAgent), Guid.NewGuid().ToString());
        BasicMessage input = new() { Content = "Hello" };
        Task testTask = fixture.RunSendTestAsync(targetAgent, input).AsTask();

        // We do not actually expect to wait the timeout here, but it is still better than waiting the 10 min
        // timeout that the tests default to. A failure will fail regardless of what timeout value we set.
        TimeSpan timeout = Debugger.IsAttached ? TimeSpan.FromSeconds(120) : TimeSpan.FromSeconds(10);
        Task timeoutTask = Task.Delay(timeout);

        Task completedTask = await Task.WhenAny([testTask, timeoutTask]);
        completedTask.Should().Be(testTask, "SendOnAgent should complete before timeout");

        // Check that each of the target agents received the message
        foreach (Guid targetKey in targetGuids)
        {
            AgentId targetId = new(nameof(ReceiverAgent), targetKey.ToString());
            receiverAgents[targetId].Messages.Should().ContainSingle(m => m.Content == $"@{targetKey}: {input.Content}");
        }
    }
}
