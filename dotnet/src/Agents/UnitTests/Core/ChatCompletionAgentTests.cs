// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Unit testing of <see cref="ChatCompletionAgent"/>.
/// </summary>
public class ChatCompletionAgentTests
{
    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Fact]
    public void VerifyChatCompletionAgentDefinition()
    {
        // Arrange
        ChatCompletionAgent agent =
            new()
            {
                Description = "test description",
                Instructions = "test instructions",
                Name = "test name",
            };

        // Assert
        Assert.NotNull(agent.Id);
        Assert.Equal("test instructions", agent.Instructions);
        Assert.Equal("test description", agent.Description);
        Assert.Equal("test name", agent.Name);
        Assert.Null(agent.Arguments);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Fact]
    public void VerifyChatCompletionAgentDefinitionWithArguments()
    {
        // Arrange
        KernelArguments arguments = new() { { "prop1", "val1" } };

        ChatCompletionAgent agent =
            new()
            {
                Description = "test description",
                Instructions = "test instructions",
                Name = "test name",
                Arguments = arguments
            };

        // Assert
        Assert.NotNull(agent.Id);
        Assert.Equal("test instructions", agent.Instructions);
        Assert.Equal("test description", agent.Description);
        Assert.Equal("test name", agent.Name);
        Assert.NotNull(agent.Arguments);
        Assert.Equal(arguments, agent.Arguments);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Fact]
    public void VerifyChatCompletionAgentTemplate()
    {
        PromptTemplateConfig promptConfig =
            new()
            {
                Name = "TestName",
                Description = "TestDescription",
                Template = "TestInstructions",
                ExecutionSettings =
                {
                    {
                        PromptExecutionSettings.DefaultServiceId,
                        new PromptExecutionSettings()
                        {
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
                            ModelId = "gpt-new",
                        }
                    },
                    {
                        "manual",
                        new PromptExecutionSettings()
                        {
                            ServiceId = "manual",
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Required(),
                            ModelId = "gpt-old",
                        }
                    },
                }
            };
        KernelPromptTemplateFactory templateFactory = new();

        // Arrange
        ChatCompletionAgent agent = new(promptConfig, templateFactory);

        // Assert
        Assert.NotNull(agent.Id);
        Assert.Equal(promptConfig.Template, agent.Instructions);
        Assert.Equal(promptConfig.Description, agent.Description);
        Assert.Equal(promptConfig.Name, agent.Name);
        Assert.Equal(promptConfig.ExecutionSettings, agent.Arguments?.ExecutionSettings);
    }

    /// <summary>
    /// Verify throws <see cref="KernelException"/> when invalid <see cref="IPromptTemplateFactory"/> is provided.
    /// </summary>
    [Fact]
    public void VerifyThrowsForInvalidTemplateFactory()
    {
        // Arrange
        PromptTemplateConfig promptConfig =
            new()
            {
                Name = "TestName",
                Description = "TestDescription",
                Template = "TestInstructions",
                TemplateFormat = "handlebars",
            };
        KernelPromptTemplateFactory templateFactory = new();

        // Act and Assert
        Assert.Throws<KernelException>(() => new ChatCompletionAgent(promptConfig, templateFactory));
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyChatCompletionAgentInvocationAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockService = new();
        mockService.Setup(
            s => s.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>())).ReturnsAsync([new(AuthorRole.Assistant, "what?")]);

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = CreateKernel(mockService.Object),
                Arguments = [],
            };

        // Act
        AgentResponseItem<ChatMessageContent>[] result = await agent.InvokeAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>).ToArrayAsync();

        // Assert
        Assert.Single(result);

        mockService.Verify(
            x =>
                x.GetChatMessageContentsAsync(
                    It.IsAny<ChatHistory>(),
                    It.IsAny<PromptExecutionSettings>(),
                    It.IsAny<Kernel>(),
                    It.IsAny<CancellationToken>()),
            Times.Once);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyChatCompletionAgentInvocationsCanMutateProvidedKernelAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockService = new();
        mockService.Setup(
            s => s.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>())).ReturnsAsync([new(AuthorRole.Assistant, "what?")]);

        var kernel = CreateKernel(mockService.Object);
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = kernel,
                Arguments = [],
            };

        // Act
        AgentResponseItem<ChatMessageContent>[] result = await agent.InvokeAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>).ToArrayAsync();

        // Assert
        Assert.Single(result);

        mockService.Verify(
            x =>
                x.GetChatMessageContentsAsync(
                    It.IsAny<ChatHistory>(),
                    It.IsAny<PromptExecutionSettings>(),
                    kernel, // Use the same kernel instance
                    It.IsAny<CancellationToken>()),
            Times.Once);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent"/> using <see cref="IChatClient"/>.
    /// </summary>
    [Fact]
    public async Task VerifyChatClientAgentInvocationAsync()
    {
        // Arrange
        Mock<IChatClient> mockService = new();
        mockService.Setup(
            s => s.GetResponseAsync(
                It.IsAny<IEnumerable<ChatMessage>>(),
                It.IsAny<ChatOptions>(),
                It.IsAny<CancellationToken>())).ReturnsAsync(new ChatResponse([new(ChatRole.Assistant, "what?")]));

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = CreateKernel(mockService.Object),
                Arguments = new(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        // Act
        AgentResponseItem<ChatMessageContent>[] result = await agent.InvokeAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>).ToArrayAsync();

        // Assert
        Assert.Single(result);

        mockService.Verify(
            x =>
                x.GetResponseAsync(
                    It.IsAny<IEnumerable<ChatMessage>>(),
                    It.Is<ChatOptions>(o => GetKernelFromChatOptions(o) == agent.Kernel),
                    It.IsAny<CancellationToken>()),
            Times.Once);
    }

    /// <summary>
    /// Verify the streaming invocation and response of <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyChatCompletionAgentStreamingAsync()
    {
        // Arrange
        StreamingChatMessageContent[] returnContent =
            [
                new(AuthorRole.Assistant, "wh"),
                new(AuthorRole.Assistant, "at?"),
            ];

        Mock<IChatCompletionService> mockService = new();
        mockService.Setup(
            s => s.GetStreamingChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>())).Returns(returnContent.ToAsyncEnumerable());

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = CreateKernel(mockService.Object),
                Arguments = [],
            };

        // Act
        AgentResponseItem<StreamingChatMessageContent>[] result = await agent.InvokeStreamingAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>).ToArrayAsync();

        // Assert
        Assert.Equal(2, result.Length);

        mockService.Verify(
            x =>
                x.GetStreamingChatMessageContentsAsync(
                    It.IsAny<ChatHistory>(),
                    It.IsAny<PromptExecutionSettings>(),
                    It.IsAny<Kernel>(),
                    It.IsAny<CancellationToken>()),
            Times.Once);
    }

    /// <summary>
    /// Verify the streaming invocation and response of <see cref="ChatCompletionAgent"/>.
    /// </summary>
    [Fact]
    public async Task VerifyChatCompletionAgentStreamingCanMutateProvidedKernelAsync()
    {
        // Arrange
        StreamingChatMessageContent[] returnContent =
            [
                new(AuthorRole.Assistant, "wh"),
                new(AuthorRole.Assistant, "at?"),
            ];

        Mock<IChatCompletionService> mockService = new();
        mockService.Setup(
            s => s.GetStreamingChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>())).Returns(returnContent.ToAsyncEnumerable());

        var kernel = CreateKernel(mockService.Object);
        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = kernel,
                Arguments = [],
            };

        // Act
        AgentResponseItem<StreamingChatMessageContent>[] result = await agent.InvokeStreamingAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>).ToArrayAsync();

        // Assert
        Assert.Equal(2, result.Length);

        mockService.Verify(
            x =>
                x.GetStreamingChatMessageContentsAsync(
                    It.IsAny<ChatHistory>(),
                    It.IsAny<PromptExecutionSettings>(),
                    kernel, // Use the same kernel instance
                    It.IsAny<CancellationToken>()),
            Times.Once);
    }

    /// <summary>
    /// Verify the streaming invocation and response of <see cref="ChatCompletionAgent"/> using <see cref="IChatClient"/>.
    /// </summary>
    [Fact]
    public async Task VerifyChatClientAgentStreamingAsync()
    {
        // Arrange
        ChatResponseUpdate[] returnUpdates =
        [
            new ChatResponseUpdate(role: ChatRole.Assistant, content: "wh"),
            new ChatResponseUpdate(role: null, content: "at?"),
        ];

        Mock<IChatClient> mockService = new();
        mockService.Setup(
            s => s.GetStreamingResponseAsync(
                It.IsAny<IEnumerable<ChatMessage>>(),
                It.IsAny<ChatOptions>(),
                It.IsAny<CancellationToken>())).Returns(returnUpdates.ToAsyncEnumerable());

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = CreateKernel(mockService.Object),
                Arguments = new(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
            };

        // Act
        AgentResponseItem<StreamingChatMessageContent>[] result = await agent.InvokeStreamingAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>).ToArrayAsync();

        // Assert
        Assert.Equal(2, result.Length);

        mockService.Verify(
            x =>
                x.GetStreamingResponseAsync(
                    It.IsAny<IEnumerable<ChatMessage>>(),
                    It.Is<ChatOptions>(o => GetKernelFromChatOptions(o) == agent.Kernel),
                    It.IsAny<CancellationToken>()),
            Times.Once);
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent.GetChatCompletionService"/>.
    /// </summary>
    [Fact]
    public void VerifyChatCompletionServiceSelection()
    {
        // Arrange
        Mock<IChatCompletionService> mockService = new();
        Kernel kernel = CreateKernel(mockService.Object);

        // Act
        (IChatCompletionService service, PromptExecutionSettings? settings) = ChatCompletionAgent.GetChatCompletionService(kernel, null);
        // Assert
        Assert.Equal(mockService.Object, service);
        Assert.Null(settings);

        // Act
        (service, settings) = ChatCompletionAgent.GetChatCompletionService(kernel, []);
        // Assert
        Assert.Equal(mockService.Object, service);
        Assert.Null(settings);

        // Act and Assert
        Assert.Throws<KernelException>(() => ChatCompletionAgent.GetChatCompletionService(kernel, new KernelArguments(new PromptExecutionSettings() { ServiceId = "anything" })));
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent.GetChatCompletionService"/> using <see cref="IChatClient"/>.
    /// </summary>
    [Fact]
    public void VerifyChatClientSelection()
    {
        // Arrange
        Mock<IChatClient> mockClient = new();
        Kernel kernel = CreateKernel(mockClient.Object);

        // Act
        (IChatCompletionService client, PromptExecutionSettings? settings) = ChatCompletionAgent.GetChatCompletionService(kernel, null);
        // Assert
        Assert.Equal("ChatClientChatCompletionService", client.GetType().Name);
        Assert.Null(settings);

        // Act
        (client, settings) = ChatCompletionAgent.GetChatCompletionService(kernel, []);
        // Assert
        Assert.Equal("ChatClientChatCompletionService", client.GetType().Name);
        Assert.Null(settings);

        // Act and Assert
        Assert.Throws<KernelException>(() => ChatCompletionAgent.GetChatCompletionService(kernel, new KernelArguments(new PromptExecutionSettings() { ServiceId = "anything" })));
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent.GetChatCompletionService"/>.
    /// </summary>
    [Fact]
    public void VerifyChatCompletionChannelKeys()
    {
        // Arrange
        ChatCompletionAgent agent1 = new();
        ChatCompletionAgent agent2 = new();
        ChatCompletionAgent agent3 = new() { HistoryReducer = new ChatHistoryTruncationReducer(50) };
        ChatCompletionAgent agent4 = new() { HistoryReducer = new ChatHistoryTruncationReducer(50) };
        ChatCompletionAgent agent5 = new() { HistoryReducer = new ChatHistoryTruncationReducer(100) };

        // Act ans Assert
        Assert.Equal(agent1.GetChannelKeys(), agent2.GetChannelKeys());
        Assert.Equal(agent3.GetChannelKeys(), agent4.GetChannelKeys());
        Assert.NotEqual(agent1.GetChannelKeys(), agent3.GetChannelKeys());
        Assert.NotEqual(agent3.GetChannelKeys(), agent5.GetChannelKeys());
    }

    /// <summary>
    /// Verify that InvalidOperationException is thrown when UseImmutableKernel is false and AIFunctions exist.
    /// </summary>
    [Fact]
    public async Task VerifyChatCompletionAgentThrowsWhenUseImmutableKernelFalseWithAIFunctionsAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockService = new();
        mockService.Setup(
            s => s.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>())).ReturnsAsync([new(AuthorRole.Assistant, "what?")]);

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = CreateKernel(mockService.Object),
                Arguments = [],
                UseImmutableKernel = false // Explicitly set to false
            };

        var thread = new ChatHistoryAgentThread();
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            async () => await agent.InvokeAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>, thread: thread).ToArrayAsync());

        Assert.NotNull(exception);
    }

    /// <summary>
    /// Verify that InvalidOperationException is thrown when UseImmutableKernel is default (false) and AIFunctions exist.
    /// </summary>
    [Fact]
    public async Task VerifyChatCompletionAgentThrowsWhenUseImmutableKernelDefaultWithAIFunctionsAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockService = new();
        mockService.Setup(
            s => s.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>())).ReturnsAsync([new(AuthorRole.Assistant, "what?")]);

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = CreateKernel(mockService.Object),
                Arguments = []
                // UseImmutableKernel not set, should default to false
            };

        var thread = new ChatHistoryAgentThread();
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            async () => await agent.InvokeAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>, thread: thread).ToArrayAsync());

        Assert.NotNull(exception);
    }

    /// <summary>
    /// Verify that kernel remains immutable when UseImmutableKernel is true.
    /// </summary>
    [Fact]
    public async Task VerifyChatCompletionAgentKernelImmutabilityWhenUseImmutableKernelTrueAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockService = new();
        Kernel capturedKernel = null!;
        mockService.Setup(
            s => s.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>()))
            .Callback<ChatHistory, PromptExecutionSettings, Kernel, CancellationToken>((_, _, kernel, _) => capturedKernel = kernel)
            .ReturnsAsync([new(AuthorRole.Assistant, "what?")]);

        var originalKernel = CreateKernel(mockService.Object);
        var originalPluginCount = originalKernel.Plugins.Count;

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [new TestAIFunction("TestFunction", "Test function description")]
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = originalKernel,
                Arguments = [],
                UseImmutableKernel = true
            };

        var thread = new ChatHistoryAgentThread();
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        // Act
        AgentResponseItem<ChatMessageContent>[] result = await agent.InvokeAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>, thread: thread).ToArrayAsync();

        // Assert
        Assert.Single(result);

        // Verify original kernel was not modified
        Assert.Equal(originalPluginCount, originalKernel.Plugins.Count);

        // Verify a different kernel instance was used for the service call
        Assert.NotSame(originalKernel, capturedKernel);

        // Verify the captured kernel has the additional plugin from AIContext
        Assert.True(capturedKernel.Plugins.Count > originalPluginCount);
        Assert.Contains(capturedKernel.Plugins, p => p.Name == "Tools");
    }

    /// <summary>
    /// Verify that mutable kernel behavior works when UseImmutableKernel is false and no AIFunctions exist.
    /// </summary>
    [Fact]
    public async Task VerifyChatCompletionAgentMutableKernelWhenUseImmutableKernelFalseNoAIFunctionsAsync()
    {
        // Arrange
        Mock<IChatCompletionService> mockService = new();
        Kernel capturedKernel = null!;
        mockService.Setup(
            s => s.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>()))
            .Callback<ChatHistory, PromptExecutionSettings, Kernel, CancellationToken>((_, _, kernel, _) => capturedKernel = kernel)
            .ReturnsAsync([new(AuthorRole.Assistant, "what?")]);

        var originalKernel = CreateKernel(mockService.Object);

        var mockAIContextProvider = new Mock<AIContextProvider>();
        var aiContext = new AIContext
        {
            AIFunctions = [] // Empty AIFunctions list
        };
        mockAIContextProvider.Setup(p => p.ModelInvokingAsync(It.IsAny<ICollection<ChatMessage>>(), It.IsAny<CancellationToken>()))
                           .ReturnsAsync(aiContext);

        ChatCompletionAgent agent =
            new()
            {
                Instructions = "test instructions",
                Kernel = originalKernel,
                Arguments = [],
                UseImmutableKernel = false
            };

        var thread = new ChatHistoryAgentThread();
        thread.AIContextProviders.Add(mockAIContextProvider.Object);

        // Act
        AgentResponseItem<ChatMessageContent>[] result = await agent.InvokeAsync(Array.Empty<ChatMessageContent>() as ICollection<ChatMessageContent>, thread: thread).ToArrayAsync();

        // Assert
        Assert.Single(result);

        // Verify the same kernel instance was used (mutable behavior)
        Assert.Same(originalKernel, capturedKernel);
    }

    private static Kernel CreateKernel(IChatCompletionService chatCompletionService)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(chatCompletionService);
        return builder.Build();
    }

    private static Kernel CreateKernel(IChatClient chatClient)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatClient>(chatClient);
        return builder.Build();
    }

    /// <summary>
    /// Gets the Kernel property from ChatOptions using reflection.
    /// </summary>
    /// <param name="options">The ChatOptions instance to extract Kernel from.</param>
    /// <returns>The Kernel instance if found; otherwise, null.</returns>
    private static Kernel? GetKernelFromChatOptions(ChatOptions options)
    {
        // Use reflection to try to get the Kernel property
        var kernelProperty = options.GetType().GetProperty("Kernel",
            System.Reflection.BindingFlags.Public |
            System.Reflection.BindingFlags.NonPublic |
            System.Reflection.BindingFlags.Instance);

        if (kernelProperty != null)
        {
            return kernelProperty.GetValue(options) as Kernel;
        }

        return null;
    }

    /// <summary>
    /// Helper class for testing AIFunction behavior.
    /// </summary>
    private sealed class TestAIFunction : AIFunction
    {
        public TestAIFunction(string name, string description = "")
        {
            this.Name = name;
            this.Description = description;
        }

        public override string Name { get; }

        public override string Description { get; }

        protected override ValueTask<object?> InvokeCoreAsync(AIFunctionArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            return ValueTask.FromResult<object?>("Test result");
        }
    }
}
