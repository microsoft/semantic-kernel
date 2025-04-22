// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using FluentAssertions;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.InProcess.Tests;

[Trait("Category", "Unit")]
public class PublishMessageTests
{
    [Fact]
    public async Task Test_PublishMessage_Success()
    {
        MessagingTestFixture fixture = new();

        await fixture.RegisterReceiverAgent(topicTypes: "TestTopic");
        await fixture.RegisterReceiverAgent("2", topicTypes: "TestTopic");

        await fixture.RunPublishTestAsync(new TopicId("TestTopic"), new BasicMessage { Content = "1" });

        fixture.GetAgentInstances<ReceiverAgent>().Values
            .Should().HaveCount(2, "Two agents should have been created")
                 .And.AllSatisfy(receiverAgent => receiverAgent.Messages
                                                               .Should().NotBeNull()
                                                                    .And.HaveCount(1)
                                                                    .And.ContainSingle(m => m.Content == "1"));
    }

    [Fact]
    public async Task Test_PublishMessage_SingleFailure()
    {
        MessagingTestFixture fixture = new();

        await fixture.RegisterErrorAgent(topicTypes: "TestTopic");

        Func<Task> publishTask = async () => await fixture.RunPublishTestAsync(new TopicId("TestTopic"), new BasicMessage { Content = "1" });

        // Test that we wrap single errors appropriately
        await publishTask.Should().ThrowAsync<TestException>();

        fixture.GetAgentInstances<ErrorAgent>().Values.Should().ContainSingle()
                                                .Which.DidThrow.Should().BeTrue("Agent should have thrown an exception");
    }

    [Fact]
    public async Task Test_PublishMessage_MultipleFailures()
    {
        MessagingTestFixture fixture = new();

        await fixture.RegisterErrorAgent(topicTypes: "TestTopic");
        await fixture.RegisterErrorAgent("2", topicTypes: "TestTopic");

        Func<Task> publishTask = async () => await fixture.RunPublishTestAsync(new TopicId("TestTopic"), new BasicMessage { Content = "1" });

        // What we are really testing here is that a single exception does not prevent sending to the remaining agents
        (await publishTask.Should().ThrowAsync<AggregateException>())
                                   .Which.Should().Match<AggregateException>(
                                        exception => exception.InnerExceptions.Count == 2 &&
                                              exception.InnerExceptions.All(exception => exception is TestException));

        fixture.GetAgentInstances<ErrorAgent>().Values
            .Should().HaveCount(2)
                 .And.AllSatisfy(
                    agent => agent.DidThrow.Should().BeTrue("Agent should have thrown an exception"));
    }

    [Fact]
    public async Task Test_PublishMessage_MixedSuccessFailure()
    {
        MessagingTestFixture fixture = new();

        await fixture.RegisterReceiverAgent(topicTypes: "TestTopic");
        await fixture.RegisterReceiverAgent("2", topicTypes: "TestTopic");

        await fixture.RegisterErrorAgent(topicTypes: "TestTopic");
        await fixture.RegisterErrorAgent("2", topicTypes: "TestTopic");

        Func<Task> publicTask = async () => await fixture.RunPublishTestAsync(new TopicId("TestTopic"), new BasicMessage { Content = "1" });

        // What we are really testing here is that raising exceptions does not prevent sending to the remaining agents
        (await publicTask.Should().ThrowAsync<AggregateException>())
                                   .Which.Should().Match<AggregateException>(
                                        exception => exception.InnerExceptions.Count == 2 &&
                                              exception.InnerExceptions.All(
                                                exception => exception is TestException));

        fixture.GetAgentInstances<ReceiverAgent>().Values
            .Should().HaveCount(2, "Two ReceiverAgents should have been created")
                 .And.AllSatisfy(receiverAgent => receiverAgent.Messages
                                                               .Should().NotBeNull()
                                                                    .And.HaveCount(1)
                                                                    .And.ContainSingle(m => m.Content == "1"),
                                 "ReceiverAgents should get published message regardless of ErrorAgents throwing exception.");

        fixture.GetAgentInstances<ErrorAgent>().Values
            .Should().HaveCount(2, "Two ErrorAgents should have been created")
                 .And.AllSatisfy(agent => agent.DidThrow.Should().BeTrue("ErrorAgent should have thrown an exception"));
    }

    [Fact]
    public async Task Test_PublishMessage_RecurrentPublishSucceeds()
    {
        MessagingTestFixture fixture = new();

        await fixture.RegisterFactoryMapInstances(
            nameof(PublisherAgent),
            (id, runtime) => ValueTask.FromResult(new PublisherAgent(id, runtime, string.Empty, [new TopicId("TestTopic")])));

        await fixture.Runtime.AddSubscriptionAsync(new TestSubscription("RunTest", nameof(PublisherAgent)));

        await fixture.RegisterReceiverAgent(topicTypes: "TestTopic");
        await fixture.RegisterReceiverAgent("2", topicTypes: "TestTopic");

        await fixture.RunPublishTestAsync(new TopicId("RunTest"), new BasicMessage { Content = "1" });

        TopicId testTopicId = new("TestTopic");
        fixture.GetAgentInstances<ReceiverAgent>().Values
            .Should().HaveCount(2, "Two ReceiverAgents should have been created")
                 .And.AllSatisfy(receiverAgent => receiverAgent.Messages
                                                               .Should().NotBeNull()
                                                                    .And.HaveCount(1)
                                                                    .And.ContainSingle(m => m.Content == $"@{testTopicId}: 1"));
    }
}
