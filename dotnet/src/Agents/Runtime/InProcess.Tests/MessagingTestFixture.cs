// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Runtime.InProcess.Tests;

public sealed class BasicMessage
{
    public string Content { get; set; } = string.Empty;
}

#pragma warning disable RCS1194 // Implement exception constructors
public sealed class TestException : Exception { }
#pragma warning restore RCS1194 // Implement exception constructors

public sealed class PublisherAgent : TestAgent, IHandle<BasicMessage>
{
    private readonly IList<TopicId> targetTopics;

    public PublisherAgent(AgentId id, IAgentRuntime runtime, string description, IList<TopicId> targetTopics)
        : base(id, runtime, description)
    {
        this.targetTopics = targetTopics;
    }

    public async ValueTask HandleAsync(BasicMessage item, MessageContext messageContext)
    {
        this.ReceivedMessages.Add(item);
        foreach (TopicId targetTopic in this.targetTopics)
        {
            await this.PublishMessageAsync(
                new BasicMessage { Content = $"@{targetTopic}: {item.Content}" },
                targetTopic);
        }
    }
}

public sealed class SendOnAgent : TestAgent, IHandle<BasicMessage>
{
    private readonly IList<Guid> targetKeys;

    public SendOnAgent(AgentId id, IAgentRuntime runtime, string description, IList<Guid> targetKeys)
        : base(id, runtime, description)
    {
        this.targetKeys = targetKeys;
    }

    public async ValueTask HandleAsync(BasicMessage item, MessageContext messageContext)
    {
        foreach (Guid targetKey in this.targetKeys)
        {
            AgentId targetId = new(nameof(ReceiverAgent), targetKey.ToString());
            BasicMessage response = new() { Content = $"@{targetKey}: {item.Content}" };
            await this.SendMessageAsync(response, targetId);
        }
    }
}

public sealed class ReceiverAgent : TestAgent, IHandle<BasicMessage>
{
    public List<BasicMessage> Messages { get; } = [];

    public ReceiverAgent(AgentId id, IAgentRuntime runtime, string description)
        : base(id, runtime, description)
    {
    }

    public ValueTask HandleAsync(BasicMessage item, MessageContext messageContext)
    {
        this.Messages.Add(item);
        return ValueTask.CompletedTask;
    }
}

public sealed class ProcessorAgent : TestAgent, IHandle<BasicMessage, BasicMessage>
{
    private Func<string, string> ProcessFunc { get; }

    public ProcessorAgent(AgentId id, IAgentRuntime runtime, Func<string, string> processFunc, string description)
        : base(id, runtime, description)
    {
        this.ProcessFunc = processFunc;
    }

    public ValueTask<BasicMessage> HandleAsync(BasicMessage item, MessageContext messageContext)
    {
        BasicMessage result = new() { Content = this.ProcessFunc.Invoke(((BasicMessage)item).Content) };

        return ValueTask.FromResult(result);
    }
}

public sealed class CancelAgent : TestAgent, IHandle<BasicMessage>
{
    public CancelAgent(AgentId id, IAgentRuntime runtime, string description)
        : base(id, runtime, description)
    {
    }

    public ValueTask HandleAsync(BasicMessage item, MessageContext messageContext)
    {
        CancellationToken cancelledToken = new(canceled: true);
        cancelledToken.ThrowIfCancellationRequested();

        return ValueTask.CompletedTask;
    }
}

public sealed class ErrorAgent : TestAgent, IHandle<BasicMessage>
{
    public ErrorAgent(AgentId id, IAgentRuntime runtime, string description)
        : base(id, runtime, description)
    {
    }

    public bool DidThrow { get; private set; }

    public ValueTask HandleAsync(BasicMessage item, MessageContext messageContext)
    {
        this.DidThrow = true;

        throw new TestException();
    }
}

public sealed class MessagingTestFixture
{
    private Dictionary<Type, object> AgentsTypeMap { get; } = [];
    public InProcessRuntime Runtime { get; } = new();

    public ValueTask<AgentType> RegisterFactoryMapInstances<TAgent>(AgentType type, Func<AgentId, IAgentRuntime, ValueTask<TAgent>> factory)
        where TAgent : IHostableAgent
    {
        async ValueTask<TAgent> WrappedFactory(AgentId id, IAgentRuntime runtime)
        {
            TAgent agent = await factory(id, runtime);
            this.GetAgentInstances<TAgent>()[id] = agent;
            return agent;
        }

        return this.Runtime.RegisterAgentFactoryAsync(type, WrappedFactory);
    }

    public Dictionary<AgentId, TAgent> GetAgentInstances<TAgent>() where TAgent : IHostableAgent
    {
        if (!this.AgentsTypeMap.TryGetValue(typeof(TAgent), out object? maybeAgentMap) ||
            maybeAgentMap is not Dictionary<AgentId, TAgent> result)
        {
            this.AgentsTypeMap[typeof(TAgent)] = result = [];
        }

        return result;
    }
    public async ValueTask RegisterReceiverAgent(string? agentNameSuffix = null, params string[] topicTypes)
    {
        await this.RegisterFactoryMapInstances(
            $"{nameof(ReceiverAgent)}{agentNameSuffix ?? string.Empty}",
            (id, runtime) => ValueTask.FromResult(new ReceiverAgent(id, runtime, string.Empty)));

        foreach (string topicType in topicTypes)
        {
            await this.Runtime.AddSubscriptionAsync(new TestSubscription(topicType, $"{nameof(ReceiverAgent)}{agentNameSuffix ?? string.Empty}"));
        }
    }

    public async ValueTask RegisterErrorAgent(string? agentNameSuffix = null, params string[] topicTypes)
    {
        await this.RegisterFactoryMapInstances(
            $"{nameof(ErrorAgent)}{agentNameSuffix ?? string.Empty}",
            (id, runtime) => ValueTask.FromResult(new ErrorAgent(id, runtime, string.Empty)));

        foreach (string topicType in topicTypes)
        {
            await this.Runtime.AddSubscriptionAsync(new TestSubscription(topicType, $"{nameof(ErrorAgent)}{agentNameSuffix ?? string.Empty}"));
        }
    }

    public async ValueTask RunPublishTestAsync(TopicId sendTarget, object message, string? messageId = null)
    {
        messageId ??= Guid.NewGuid().ToString();

        await this.Runtime.StartAsync();
        await this.Runtime.PublishMessageAsync(message, sendTarget, messageId: messageId);
        await this.Runtime.RunUntilIdleAsync();
    }

    public async ValueTask<object?> RunSendTestAsync(AgentId sendTarget, object message, string? messageId = null)
    {
        messageId ??= Guid.NewGuid().ToString();

        await this.Runtime.StartAsync();

        object? result = await this.Runtime.SendMessageAsync(message, sendTarget, messageId: messageId);

        await this.Runtime.RunUntilIdleAsync();

        return result;
    }
}
