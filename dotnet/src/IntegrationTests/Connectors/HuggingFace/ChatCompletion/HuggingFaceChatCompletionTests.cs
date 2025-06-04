// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.HuggingFace.ChatCompletion;

/// <summary>
/// Integration tests for <see cref="HuggingFaceChatCompletionService"/>.
/// </summary>
/// <remarks>
/// Instructions for setting up a Text Generation Inference (TGI) endpoint, see: https://huggingface.co/blog/tgi-messages-api
/// </remarks>
public sealed class HuggingFaceChatCompletionTests(ITestOutputHelper output) : HuggingFaceTestsBase(output)
{
    [Fact(Skip = "This test is for manual verification.")]
    public async Task GetChatMessageContentsAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Use C# 12 features."),
            new ChatMessageContent(AuthorRole.User, "Write a C# Hello world?")
        };
        var huggingFaceRemote = this.CreateChatCompletionService();

        // Act
        var response = await huggingFaceRemote.GetChatMessageContentsAsync(chatHistory, new HuggingFacePromptExecutionSettings() { MaxNewTokens = 50 });

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.True(response[0].Content?.Length > 0);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task GetStreamingChatMessageContentsAsync()
    {
        // Arrange
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.System, "Use C# 12 features."),
            new ChatMessageContent(AuthorRole.User, "Write a C# Hello world?")
        };
        var huggingFaceRemote = this.CreateChatCompletionService();

        // Act
        var response = new StringBuilder();
        await foreach (var update in huggingFaceRemote.GetStreamingChatMessageContentsAsync(chatHistory, new HuggingFacePromptExecutionSettings() { MaxNewTokens = 50 }))
        {
            if (update.Content is { Length: > 0 })
            {
                response.Append(update.Content);
            }
        }

        // Assert
        Assert.NotNull(response);
        Assert.True(response.Length > 0);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task InvokeKernelFunctionAsync()
    {
        // Arrange
        Kernel kernel = this.CreateKernelWithChatCompletion();

        var kernelFunction = kernel.CreateFunctionFromPrompt("<message role=\"user\">Write a C# Hello world</message>", new HuggingFacePromptExecutionSettings
        {
            MaxNewTokens = 50,
        });

        // Act
        var response = await kernel.InvokeAsync(kernelFunction);

        // Assert
        Assert.NotNull(response);
        Assert.True(response.ToString().Length > 0);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task InvokeKernelFunctionStreamingAsync()
    {
        // Arrange
        Kernel kernel = this.CreateKernelWithChatCompletion();

        var kernelFunction = kernel.CreateFunctionFromPrompt("<message role=\"user\">Write a C# Hello world</message>", new HuggingFacePromptExecutionSettings
        {
            MaxNewTokens = 50,
        });

        // Act
        var response = new StringBuilder();
        await foreach (var update in kernel.InvokeStreamingAsync(kernelFunction))
        {
            if (update.ToString() is { Length: > 0 })
            {
                response.Append(update);
            }
        }

        // Assert
        Assert.NotNull(response);
        Assert.True(response.ToString().Length > 0);
    }
}
