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
        Assert.Null(agent.ExecutionSettings);
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
                It.IsAny<CancellationToken>())).ReturnsAsync(new ChatMessageContent[] { new(AuthorRole.Assistant, "what?") });

        var agent =
            new ChatCompletionAgent()
            {
                Kernel = CreateKernel(mockService.Object)
            };

        var result = await agent.InvokeAsync([]).ToArrayAsync();

        mockService.Verify(
            x =>
                x.GetChatMessageContentsAsync(
                    It.IsAny<ChatHistory>(),
                    It.IsAny<PromptExecutionSettings>(),
                    It.IsAny<Kernel>(),
                    It.IsAny<CancellationToken>()),
            Times.Once);
    }

    private static Kernel CreateKernel(IChatCompletionService chatCompletionService)
    {
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<IChatCompletionService>(chatCompletionService);
        return builder.Build();
    }
}
