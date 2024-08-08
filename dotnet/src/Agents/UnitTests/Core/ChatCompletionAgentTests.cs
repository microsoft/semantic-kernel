// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.History;
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
        ChatCompletionAgent agent =
            new()
            {
                Description = "test description",
                Instructions = "test instructions",
                Name = "test name",
            };

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
    public async Task VerifyChatCompletionAgentInvocationAsync()
    {
        var mockService = new Mock<IChatCompletionService>();
        mockService.Setup(
            s => s.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>())).ReturnsAsync([new(AuthorRole.Assistant, "what?")]);

        var agent =
            new ChatCompletionAgent()
            {
                Instructions = "test instructions",
                Kernel = CreateKernel(mockService.Object),
                Arguments = [],
            };

        var result = await agent.InvokeAsync([]).ToArrayAsync();

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
        StreamingChatMessageContent[] returnContent =
            [
                new(AuthorRole.Assistant, "wh"),
                new(AuthorRole.Assistant, "at?"),
            ];

        var mockService = new Mock<IChatCompletionService>();
        mockService.Setup(
            s => s.GetStreamingChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings>(),
                It.IsAny<Kernel>(),
                It.IsAny<CancellationToken>())).Returns(returnContent.ToAsyncEnumerable());

        var agent =
            new ChatCompletionAgent()
            {
                Instructions = "test instructions",
                Kernel = CreateKernel(mockService.Object),
                Arguments = [],
            };

        var result = await agent.InvokeStreamingAsync([]).ToArrayAsync();

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
        Mock<IChatCompletionService> mockService = new();
        Kernel kernel = CreateKernel(mockService.Object);

        (IChatCompletionService service, PromptExecutionSettings? settings) = ChatCompletionAgent.GetChatCompletionService(kernel, null);
        Assert.Null(settings);

        (service, settings) = ChatCompletionAgent.GetChatCompletionService(kernel, []);
        Assert.Null(settings);

        Assert.Throws<KernelException>(() => ChatCompletionAgent.GetChatCompletionService(kernel, new KernelArguments(new PromptExecutionSettings() { ServiceId = "anything" })));
    }

    /// <summary>
    /// Verify the invocation and response of <see cref="ChatCompletionAgent.GetChatCompletionService"/>.
    /// </summary>
    [Fact]
    public void VerifyChatCompletionChannelKeys()
    {
        ChatCompletionAgent agent1 = new();
        ChatCompletionAgent agent2 = new();
        ChatCompletionAgent agent3 = new() { HistoryReducer = new ChatHistoryTruncationReducer(50) };
        ChatCompletionAgent agent4 = new() { HistoryReducer = new ChatHistoryTruncationReducer(50) };
        ChatCompletionAgent agent5 = new() { HistoryReducer = new ChatHistoryTruncationReducer(100) };

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
