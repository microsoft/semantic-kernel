// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Factory;

/// <summary>
/// Tests for <see cref="AggregatorKernelAgentFactory"/>.
/// </summary>
public class AggregatorKernelAgentFactoryTests
{
    /// <summary>
    /// Verifies that the <see cref="AggregatorKernelAgentFactory"/> can create different types of agents.
    /// </summary>
    [Fact]
    public async Task ItCreatesKernelAgentsAsync()
    {
        // Arrange
        var agentDefinition1 = new AgentDefinition() { Type = "my-type-1", Name = "my-name-1", Description = "my-description-1", Instructions = "my-instructions-1" };
        var agentDefinition2 = new AgentDefinition() { Type = "my-type-2", Name = "my-name-2", Description = "my-description-2", Instructions = "my-instructions-2" };
        var kernel = new Kernel();
        var target = new AggregatorKernelAgentFactory(new MyAgentFactory1(), new MyAgentFactory2());

        // Act
        var result1 = await target.CreateAsync(kernel, agentDefinition1);
        var result2 = await target.CreateAsync(kernel, agentDefinition2);

        // Assert
        Assert.NotNull(result1);
        Assert.True(result1 is MyAgent1);
        Assert.NotNull(result2);
        Assert.True(result2 is MyAgent2);
    }

    /// <summary>
    /// Verifies that the <see cref="AggregatorKernelAgentFactory"/> throws <see cref="KernelException"/> for an unknown agent type.
    /// </summary>
    [Fact]
    public async Task ItReturnsNullForUnknownAgentTypeAsync()
    {
        // Arrange
        var agentDefinition = new AgentDefinition() { Type = "my-type-unknown", Name = "my-name-1", Description = "my-description-1", Instructions = "my-instructions-1" };
        var kernel = new Kernel();
        var target = new AggregatorKernelAgentFactory(new MyAgentFactory1(), new MyAgentFactory2());

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () => await target.CreateAsync(kernel, agentDefinition));
    }

    #region private
    private sealed class MyAgentFactory1 : AgentFactory
    {
        public MyAgentFactory1() : base(["my-type-1"])
        {
        }

        public override async Task<Agent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, AgentCreationOptions? agentCreationOptions = null, CancellationToken cancellationToken = default)
        {
            return agentDefinition.Type != "my-type-1"
                ? null
                : (Agent)await Task.FromResult(new MyAgent1()
                {
                    Name = agentDefinition.Name,
                    Description = agentDefinition.Description,
                    Instructions = agentDefinition.Instructions,
                    Kernel = kernel,
                });
        }
    }

    private sealed class MyAgentFactory2 : AgentFactory
    {
        public MyAgentFactory2() : base(["my-type-2"])
        {
        }

        public override async Task<Agent?> TryCreateAsync(Kernel kernel, AgentDefinition agentDefinition, AgentCreationOptions? agentCreationOptions = null, CancellationToken cancellationToken = default)
        {
            return agentDefinition.Type != "my-type-2"
                ? null
                : (Agent)await Task.FromResult(new MyAgent2()
                {
                    Name = agentDefinition.Name,
                    Description = agentDefinition.Description,
                    Instructions = agentDefinition.Instructions,
                    Kernel = kernel,
                });
        }
    }

    private sealed class MyAgent1 : Agent
    {
        public MyAgent1()
        {
        }

        public override IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public override IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override IEnumerable<string> GetChannelKeys()
        {
            throw new NotImplementedException();
        }

        protected internal override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }

    private sealed class MyAgent2 : Agent
    {
        public MyAgent2()
        {
        }

        public override IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public override IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override IEnumerable<string> GetChannelKeys()
        {
            throw new NotImplementedException();
        }

        protected internal override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }
    #endregion
}
