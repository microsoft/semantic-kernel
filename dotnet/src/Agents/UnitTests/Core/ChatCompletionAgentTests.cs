// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
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
        ChatMessageContent[] result = await agent.InvokeAsync([]).ToArrayAsync();

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
        StreamingChatMessageContent[] result = await agent.InvokeStreamingAsync([]).ToArrayAsync();

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

    private static Kernel CreateKernel(IChatCompletionService chatCompletionService)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(chatCompletionService);
        return builder.Build();
    }
}
