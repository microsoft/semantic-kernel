// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

public class WhiteboardBehaviorTests
{
    private readonly Mock<IChatCompletionService> _mockChatCompletionService;
    private readonly Kernel _kernel;

    public WhiteboardBehaviorTests()
    {
        this._mockChatCompletionService = new Mock<IChatCompletionService>();
        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddKeyedSingleton<IChatCompletionService>(null, this._mockChatCompletionService.Object);
        this._kernel = kernelBuilder.Build();
    }

    [Fact]
    public async Task ShouldInvokeAIAndReturnWhiteboardMessagesInContextAsync()
    {
        // Arrange
        var sut = new WhiteboardBehavior(this._kernel);
        var chatMessage = new ChatMessage(ChatRole.User, "I want to create a presentation");

        this._mockChatCompletionService
            .Setup(service => service.GetChatMessageContentsAsync(
                It.IsAny<ChatHistory>(),
                It.IsAny<PromptExecutionSettings?>(),
                It.IsAny<Kernel?>(),
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<ChatMessageContent>
            {
                new() { Content = """["REQUIREMENT - User wants to create a presentation."]""" },
            });

        // Act
        await sut.OnNewMessageAsync(null, chatMessage);

        // Assert
        this._mockChatCompletionService.Verify(service => service.GetChatMessageContentsAsync(
            It.Is<ChatHistory>(x => x.Count == 1 && x[0].ToString().Contains("I want to create a presentation")),
            It.IsAny<PromptExecutionSettings?>(),
            It.IsAny<Kernel?>(),
            It.IsAny<CancellationToken>()), Times.Once);

        await sut.WhenProcessingCompleteAsync();
        var actualContext = await sut.OnModelInvokeAsync([chatMessage]);
        Assert.Contains("REQUIREMENT - User wants to create a presentation", actualContext);
    }
}
