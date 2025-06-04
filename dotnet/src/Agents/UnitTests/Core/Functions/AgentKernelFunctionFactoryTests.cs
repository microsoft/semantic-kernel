// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core.Functions;

/// <summary>
/// Unit testing of <see cref="AgentKernelFunctionFactory"/>.
/// </summary>
public class AgentKernelFunctionFactoryTests
{
    /// <summary>
    /// Verify calling AgentKernelFunctionFactory.CreateFromAgent.
    /// </summary>
    [Fact]
    public void VerifyCreateFromAgent()
    {
        // Arrange
        var agent = new MockAgent()
        {
            Name = "MyAgent",
            Description = "Description for MyAgent"
        };

        // Act
        var function = AgentKernelFunctionFactory.CreateFromAgent(agent);

        // Assert
        Assert.NotNull(function);
        Assert.Equal(agent.Name, function.Name);
        Assert.Equal(agent.Description, function.Description);
    }

    /// <summary>
    /// Verify calling AgentKernelFunctionFactory.CreateFromAgent with overrides.
    /// </summary>
    [Fact]
    public void VerifyCreateFromAgentWithOverrides()
    {
        // Arrange
        var agent = new MockAgent()
        {
            Name = "MyAgent",
            Description = "Description for MyAgent"
        };

        // Act
        var function = AgentKernelFunctionFactory.CreateFromAgent(
            agent,
            "MyAgentFunction",
            "Description for MyAgentFunction"
            );

        // Assert
        Assert.NotNull(function);
        Assert.Equal("MyAgentFunction", function.Name);
        Assert.Equal("Description for MyAgentFunction", function.Description);
    }

    /// <summary>
    /// Verify invoking function returned by AgentKernelFunctionFactory.CreateFromAgent.
    /// </summary>
    [Fact]
    public async Task VerifyInvokeAgentAsKernelFunctionAsync()
    {
        // Arrange
        var agent = new MockAgent()
        {
            Name = "MyAgent",
            Description = "Description for MyAgent"
        };
        var function = AgentKernelFunctionFactory.CreateFromAgent(agent);

        // Act
        var arguments = new KernelArguments
        {
            { "query", "Mock query" }
        };
        var result = await function.InvokeAsync(new(), arguments);

        // Assert
        Assert.NotNull(result);
        var items = result.GetValue<IEnumerable<ChatMessageContent>>();
        Assert.NotNull(items);
        Assert.NotEmpty(items);
        Assert.Equal("Response to: 'Mock query' with instructions: ''", items.First().ToString());
    }

    /// <summary>
    /// Verify invoking function returned by AgentKernelFunctionFactory.CreateFromAgent.
    /// </summary>
    [Fact]
    public async Task VerifyInvokeAgentAsKernelFunctionWithNoQueryAsync()
    {
        // Arrange
        var agent = new MockAgent()
        {
            Name = "MyAgent",
            Description = "Description for MyAgent"
        };
        var function = AgentKernelFunctionFactory.CreateFromAgent(agent);

        // Act
        var result = await function.InvokeAsync(new());

        // Assert
        Assert.NotNull(result);
        var items = result.GetValue<IEnumerable<ChatMessageContent>>();
        Assert.NotNull(items);
        Assert.NotEmpty(items);
        Assert.Equal("Response to: '' with instructions: ''", items.First().ToString());
    }

    /// <summary>
    /// Verify invoking function returned by AgentKernelFunctionFactory.CreateFromAgent.
    /// </summary>
    [Fact]
    public async Task VerifyInvokeAgentAsKernelFunctionWithInstructionsAsync()
    {
        // Arrange
        var agent = new MockAgent()
        {
            Name = "MyAgent",
            Description = "Description for MyAgent"
        };
        var function = AgentKernelFunctionFactory.CreateFromAgent(agent);

        // Act
        var arguments = new KernelArguments
        {
            { "query", "Mock query" },
            { "instructions", "Mock instructions" }
        };
        var result = await function.InvokeAsync(new(), arguments);

        // Assert
        Assert.NotNull(result);
        var items = result.GetValue<IEnumerable<ChatMessageContent>>();
        Assert.NotNull(items);
        Assert.NotEmpty(items);
        Assert.Equal("Response to: 'Mock query' with instructions: 'Mock instructions'", items.First().ToString());
    }

    /// <summary>
    /// Mock implementation of <see cref="Agent"/>.
    /// </summary>
    private sealed class MockAgent : Agent
    {
        public override async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            var agentThread = thread ?? new MockAgentThread();
            foreach (var message in messages)
            {
                await Task.Delay(100, cancellationToken);
                yield return new AgentResponseItem<ChatMessageContent>(new ChatMessageContent(AuthorRole.Assistant, $"Response to: '{message.Content}' with instructions: '{options?.AdditionalInstructions}'"), agentThread);
            }
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

    /// <summary>
    /// Mock implementation of <see cref="AgentThread"/>
    /// </summary>
    private sealed class MockAgentThread : AgentThread
    {
        protected override Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
        {
            return Task.FromResult<string?>("mock_thread_id");
        }

        protected override Task DeleteInternalAsync(CancellationToken cancellationToken)
        {
            return Task.CompletedTask;
        }

        protected override Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
        {
            return Task.CompletedTask;
        }
    }
}
