// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Amazon.Runtime.Endpoints;
using Amazon.Runtime.EventStreams;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Amazon.UnitTests;

/// <summary>
/// Unit tests for Bedrock Chat Completion Service.
/// </summary>
public sealed class BedrockChatCompletionServiceTests
{
    /// <summary>
    /// Checks that modelID is added to the list of service attributes when service is registered.
    /// </summary>
    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        string modelId = "amazon.titan-text-premier-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.Equal(modelId, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    /// <summary>
    /// Checks that an invalid model ID cannot create a new service.
    /// </summary>
    [Fact]
    public void ShouldThrowExceptionForInvalidModelId()
    {
        // Arrange
        string invalidModelId = "invalid_model_id";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Act
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(invalidModelId, mockBedrockApi.Object).Build();

        // Assert
        Assert.Throws<KernelException>(() =>
            kernel.GetRequiredService<IChatCompletionService>());
    }

    /// <summary>
    /// Checks that an empty model ID cannot create a new service.
    /// </summary>
    [Fact]
    public void ShouldThrowExceptionForEmptyModelId()
    {
        // Arrange
        string emptyModelId = string.Empty;
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();

        // Act
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(emptyModelId, mockBedrockApi.Object).Build();

        // Assert
        Assert.Throws<KernelException>(() =>
            kernel.GetRequiredService<IChatCompletionService>());
    }

    /// <summary>
    /// Checks that an invalid BedrockRuntime object will throw an exception.
    /// </summary>
    [Fact]
    public async Task ShouldThrowExceptionForNullBedrockRuntimeAsync()
    {
        // Arrange
        string modelId = "mistral.mistral-text-lite-v1";
        IAmazonBedrockRuntime? nullBedrockRuntime = null;
        var chatHistory = CreateSampleChatHistory();

        // Act & Assert
        await Assert.ThrowsAnyAsync<Exception>(async () =>
        {
            var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, nullBedrockRuntime).Build();
            var service = kernel.GetRequiredService<IChatCompletionService>();
            await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        }).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks that GetChatMessageContentsAsync calls and correctly handles outputs from ConverseAsync.
    /// </summary>
    [Fact]
    public async Task GetChatMessageContentsAsyncShouldReturnChatMessageContentsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("Hello, world!", ConversationRole.Assistant));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.Single(result[0].Items);
        Assert.Equal("Hello, world!", result[0].Items[0].ToString());
        Assert.NotNull(result[0].InnerContent);
    }

    /// <summary>
    /// Checks that GetStreamingChatMessageContentsAsync calls and correctly handles outputs from ConverseStreamAsync.
    /// </summary>
    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncShouldReturnStreamedChatMessageContentsAsync()
    {
        // Arrange
        string modelId = "amazon.titan-text-lite-v1";

        var content = this.GetTestResponseAsBytes("converse_stream_binary_response.bin");
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseStreamRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
#pragma warning disable CA2000 // Dispose objects before losing scope
        mockBedrockApi.Setup(m => m.ConverseStreamAsync(It.IsAny<ConverseStreamRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseStreamResponse
            {
                Stream = new ConverseStreamOutput(new MemoryStream(content))
            });
#pragma warning restore CA2000 // Dispose objects before losing scope

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        List<StreamingChatMessageContent> output = new();
        var result = service.GetStreamingChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        int iterations = 0;
        await foreach (var item in result)
        {
            iterations += 1;
            Assert.NotNull(item);
            Assert.NotNull(item.Content);
            Assert.NotNull(item.Role);
            Assert.NotNull(item.InnerContent);
            output.Add(item);
        }
        Assert.True(output.Count > 0);
        Assert.Equal(iterations, output.Count);
        Assert.NotNull(service.GetModelId());
        Assert.NotNull(service.Attributes);
    }

    /// <summary>
    /// Checks that the roles from the chat history are correctly assigned and labeled for the converse calls.
    /// </summary>
    [Fact]
    public async Task GetChatMessageContentsAsyncShouldAssignCorrectRolesAsync()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("Hello, world!", ConversationRole.Assistant));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        Assert.Single(result);
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.Single(result[0].Items);
        Assert.Equal("Hello, world!", result[0].Items[0].ToString());
    }

    /// <summary>
    /// Checks that the chat history is given the correct values through calling GetChatMessageContentsAsync.
    /// </summary>
    [Fact]
    public async Task GetChatMessageContentsAsyncShouldHaveProperChatHistoryAsync()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });

        // Set up the mock ConverseAsync to return multiple responses
        mockBedrockApi.SetupSequence(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("I'm doing well.", ConversationRole.Assistant))
            .ReturnsAsync(this.CreateConverseResponse("That's great to hear!", ConversationRole.User));

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act
        var result1 = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        var result2 = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        string? chatResult1 = result1[0].Content;
        Assert.NotNull(chatResult1);
        chatHistory.AddAssistantMessage(chatResult1);
        string? chatResult2 = result2[0].Content;
        Assert.NotNull(chatResult2);
        chatHistory.AddUserMessage(chatResult2);
        Assert.Equal(2, result1.Count + result2.Count);

        // Check the first result
        Assert.Equal(AuthorRole.Assistant, result1[0].Role);
        Assert.Single(result1[0].Items);
        Assert.Equal("I'm doing well.", result1[0].Items[0].ToString());

        // Check the second result
        Assert.Equal(AuthorRole.User, result2[0].Role);
        Assert.Single(result2[0].Items);
        Assert.Equal("That's great to hear!", result2[0].Items[0].ToString());

        // Check the chat history
        Assert.Equal(6, chatHistory.Count); // Use the Count property to get the number of messages

        Assert.Equal(AuthorRole.User, chatHistory[0].Role); // Use the indexer to access individual messages
        Assert.Equal("Hello", chatHistory[0].Items[0].ToString());

        Assert.Equal(AuthorRole.Assistant, chatHistory[1].Role);
        Assert.Equal("Hi", chatHistory[1].Items[0].ToString());

        Assert.Equal(AuthorRole.User, chatHistory[2].Role);
        Assert.Equal("How are you?", chatHistory[2].Items[0].ToString());

        Assert.Equal(AuthorRole.System, chatHistory[3].Role);
        Assert.Equal("You are an AI Assistant", chatHistory[3].Items[0].ToString());

        Assert.Equal(AuthorRole.Assistant, chatHistory[4].Role);
        Assert.Equal("I'm doing well.", chatHistory[4].Items[0].ToString());

        Assert.Equal(AuthorRole.User, chatHistory[5].Role);
        Assert.Equal("That's great to hear!", chatHistory[5].Items[0].ToString());
    }

    /// <summary>
    /// Checks that the chat history with binary content is given the correct values through calling GetChatMessageContentsAsync.
    /// </summary>
    [Fact]
    public async Task GetChatMessageContentsWithBinaryContentAsyncShouldHaveProperChatHistoryAsync()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });

        // Set up the mock ConverseAsync to return multiple responses
        mockBedrockApi.SetupSequence(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("Here is the result.", ConversationRole.Assistant));

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistoryWithBinaryContent();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);

        // Assert
        string? chatResult = result[0].Content;
        Assert.NotNull(chatResult);

        // Check the first result
        Assert.Equal(AuthorRole.Assistant, result[0].Role);
        Assert.Single(result[0].Items);
        Assert.Equal("Here is the result.", result[0].Items[0].ToString());

        // Check the chat history
        Assert.Equal(6, chatHistory.Count); // Use the Count property to get the number of messages

        Assert.Equal(AuthorRole.System, chatHistory[0].Role);
        Assert.Equal("You are an AI Assistant", chatHistory[0].Items[0].ToString());

        Assert.Equal(AuthorRole.User, chatHistory[1].Role); // Use the indexer to access individual messages
        Assert.Equal("Hello", chatHistory[1].Items[0].ToString());

        Assert.Equal(AuthorRole.Assistant, chatHistory[2].Role);
        Assert.Equal("Hi", chatHistory[2].Items[0].ToString());

        Assert.Equal(AuthorRole.User, chatHistory[3].Role);
        Assert.Equal("How are you?", chatHistory[3].Items[0].ToString());

        Assert.Equal(AuthorRole.Assistant, chatHistory[4].Role);
        Assert.Equal("Fine, thanks. How can I help?", chatHistory[4].Items[0].ToString());

        Assert.Equal(AuthorRole.User, chatHistory[5].Role);
        Assert.Collection(chatHistory[5].Items,
            c =>
            {
                Assert.IsType<TextContent>(c);
                var item = (TextContent)c;
                Assert.Equal("I need you to summarize these attachments.", item.Text);
            },
            c => Assert.IsType<ImageContent>(c),
            c => Assert.IsType<PdfContent>(c),
            c => Assert.IsType<DocxContent>(c),
            c => Assert.IsType<ImageContent>(c)
        );
    }

    /// <summary>
    /// Checks that error handling present for empty chat history.
    /// </summary>
    [Fact]
    public async Task ShouldThrowArgumentExceptionIfChatHistoryIsEmptyAsync()
    {
        // Arrange
        string modelId = "amazon.titan-embed-text-v1:0";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        var chatHistory = new ChatHistory();
        mockBedrockApi.SetupSequence(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("hi", ConversationRole.Assistant));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(
            () => service.GetChatMessageContentsAsync(chatHistory)).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks error handling for empty response output.
    /// </summary>
    [Fact]
    public async Task ShouldHandleInvalidConverseResponseAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new ConverseResponse
            {
                Output = new ConverseOutput
                {
                    Message = null // Invalid response, missing message
                },
                Metrics = new ConverseMetrics(),
                StopReason = StopReason.Max_tokens,
                Usage = new TokenUsage()
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            service.GetChatMessageContentsAsync(chatHistory)).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks error handling for invalid role mapping.
    /// </summary>
    [Fact]
    public async Task ShouldHandleInvalidRoleMappingAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("Hello", (ConversationRole)"bad_role"));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = CreateSampleChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() =>
            service.GetChatMessageContentsAsync(chatHistory)).ConfigureAwait(true);
    }

    /// <summary>
    /// Checks that the chat history is correctly handled when there are null or empty messages in the chat history, but not as the last message.
    /// </summary>
    [Fact]
    public async Task ShouldHandleEmptyChatHistoryMessagesAsync()
    {
        // Arrange
        string modelId = "anthropic.claude-chat-completion";
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(this.CreateConverseResponse("hello", ConversationRole.Assistant));
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService(modelId, mockBedrockApi.Object).Build();
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(string.Empty); // Add an empty user message
        chatHistory.AddAssistantMessage(null!); // Add a null assistant message
        chatHistory.AddUserMessage("Hi");

        // Act & Assert
        await service.GetChatMessageContentsAsync(chatHistory).ConfigureAwait(true);
        // Ensure that the method handles empty messages gracefully (e.g., by skipping them)
        // and doesn't throw an exception
    }

    private sealed class TestPlugin
    {
        [KernelFunction()]
        [Description("Given a document title, look up the corresponding document ID for it.")]
        [return: Description("The identified document if found, or an empty string if not.")]
        public string FindDocumentIdForTitle(
            [Description("The title to retrieve a corresponding ID for")]
            string title
        )
        {
            return $"{title}-{Guid.NewGuid()}";
        }
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ShouldHandleToolsInConverseRequestAsync(bool required)
    {
        // Arrange
        ConverseRequest? firstRequest = null;
        ConverseRequest? secondRequest = null;
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        mockBedrockApi.Setup(m => m.ConverseAsync(It.IsAny<ConverseRequest>(), It.IsAny<CancellationToken>()))
            .Callback((ConverseRequest request, CancellationToken token) =>
            {
                if (firstRequest == null)
                {
                    firstRequest = request;
                }
                else
                {
                    secondRequest = request;
                }
            })
            .ReturnsAsync((ConverseRequest request, CancellationToken _) =>
            {
                return secondRequest == null
                    ? new ConverseResponse
                    {
                        Output = new ConverseOutput
                        {
                            Message = new Message
                            {
                                Role = ConversationRole.Assistant,
                                Content = [ new() { ToolUse = new ToolUseBlock
                            {
                                ToolUseId = "tool-use-id-1",
                                Name = "TestPlugin-FindDocumentIdForTitle",
                                Input = Document.FromObject(new Dictionary<string, object>
                                {
                                    ["title"] = "Green Eggs and Ham",
                                }),
                            } } ]
                            },
                        },
                        Metrics = new ConverseMetrics(),
                        StopReason = StopReason.Tool_use,
                        Usage = new TokenUsage()
                    }
                    : this.CreateConverseResponse("Hello, world!", ConversationRole.Assistant);
            });
        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0", mockBedrockApi.Object).Build();
        var plugin = new TestPlugin();
        kernel.ImportPluginFromObject(plugin);
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Find the ID corresponding to the title 'Green Eggs and Ham', by Dr. Suess.");
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var executionSettings = AmazonClaudeExecutionSettings.FromExecutionSettings(null);
        executionSettings.FunctionChoiceBehavior = required ? FunctionChoiceBehavior.Required() : FunctionChoiceBehavior.Auto();

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory, executionSettings, kernel, CancellationToken.None).ConfigureAwait(true);

        Assert.NotNull(firstRequest?.ToolConfig);
        if (required)
        {
            Assert.NotNull(firstRequest.ToolConfig.ToolChoice);
            Assert.Null(firstRequest.ToolConfig.ToolChoice.Auto);
            Assert.Equal("TestPlugin-FindDocumentIdForTitle", firstRequest.ToolConfig.ToolChoice?.Tool?.Name);
        }
        else // auto
        {
            Assert.NotNull(firstRequest.ToolConfig.ToolChoice?.Auto);
        }
        Assert.NotNull(secondRequest?.Messages.Last().Content?.FirstOrDefault(c => c.ToolResult != null));
    }

    [Fact(Skip = "This test is missing the binary stream containing the delta block events with tool use needed to test this API")]
    public async Task ShouldHandleToolsInConverseStreamingRequestAsync()
    {
        // Arrange
        ConverseStreamRequest? firstRequest = null;
        ConverseStreamRequest? secondRequest = null;
        var mockBedrockApi = new Mock<IAmazonBedrockRuntime>();
        mockBedrockApi.Setup(m => m.DetermineServiceOperationEndpoint(It.IsAny<ConverseStreamRequest>()))
            .Returns(new Endpoint("https://bedrock-runtime.us-east-1.amazonaws.com")
            {
                URL = "https://bedrock-runtime.us-east-1.amazonaws.com"
            });
        List<IEventStreamEvent> firstSequence = [
            new ContentBlockStartEvent
            {
                ContentBlockIndex = 0,
                Start = new ContentBlockStart
                {
                    ToolUse = new ToolUseBlockStart
                    {
                        ToolUseId = "tool-use-id-1",
                        Name = "TestPlugin-FindDocumentIdForTitle",
                    }
                }
            },
            new ContentBlockDeltaEvent
            {
                ContentBlockIndex = 1,
                Delta = new ContentBlockDelta
                {
                    ToolUse = new ToolUseBlockDelta
                    {
                        Input = """
                                {
                                    "title": "Green Eggs and Ham"
                                }
                                """,
                    }
                }
            },
            new ContentBlockStopEvent
            {
                ContentBlockIndex = 2,
            }
        ];
        mockBedrockApi.Setup(m => m.ConverseStreamAsync(It.IsAny<ConverseStreamRequest>(), It.IsAny<CancellationToken>()))
            .Callback((ConverseStreamRequest request, CancellationToken token) =>
            {
                if (firstRequest == null)
                {
                    firstRequest = request;
                }
                else
                {
                    secondRequest = request;
                }
            })
            .ReturnsAsync((ConverseStreamRequest request, CancellationToken _) =>
            {
                return new ConverseStreamResponse
                {
                    HttpStatusCode = System.Net.HttpStatusCode.OK,
                    // TODO: Replace with actual stream containing the delta block events with tool use
                    Stream = new ConverseStreamOutput(new MemoryStream())
                };
            });

        var kernel = Kernel.CreateBuilder().AddBedrockChatCompletionService("amazon.titan-text-premier-v1:0", mockBedrockApi.Object).Build();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Stream the ID corresponding to the title 'Green Eggs and Ham', by Dr. Suess.");
        var service = kernel.GetRequiredService<IChatCompletionService>();
        var executionSettings = new AmazonClaudeExecutionSettings
        {
            ModelId = "amazon.titan-text-premier-v1:0",
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
        };

        // Act
        var result = service.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, CancellationToken.None).ConfigureAwait(true);
        var stream = new List<StreamingChatMessageContent>();
        await foreach (var msg in result)
        {
            stream.Add(msg);
        }

        // Assert
        Assert.NotNull(firstRequest?.ToolConfig);
        Assert.NotNull(secondRequest?.Messages.Last().Content?.FirstOrDefault(c => c.ToolResult != null));
    }

    private static ChatHistory CreateSampleChatHistory()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        chatHistory.AddSystemMessage("You are an AI Assistant");
        return chatHistory;
    }

    private static ChatHistory CreateSampleChatHistoryWithBinaryContent()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("You are an AI Assistant");
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        chatHistory.AddAssistantMessage("Fine, thanks. How can I help?");
        chatHistory.AddUserMessage(
        [
            new TextContent("I need you to summarize these attachments."),
            new ImageContent(new Uri("https://example.com/image.jpg")),
            new PdfContent(GetTestDataFileContentsAsBase64String("SemanticKernelCookBook.en.pdf", "application/pdf")),
            new DocxContent(GetTestDataFileContentsAsBase64String("test-doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            new ImageContent(GetTestDataFileContentsAsBase64String("the-planner.png", "image/png")),
        ]);
        return chatHistory;
    }

    private byte[] GetTestResponseAsBytes(string fileName) => GetTestDataFileContentsAsBytes(fileName);

    private static byte[] GetTestDataFileContentsAsBytes(string fileName)
    {
        return File.ReadAllBytes($"TestData/{fileName}");
    }

    private static string GetTestDataFileContentsAsBase64String(string fileName, string mimeType)
    {
        var content = Convert.ToBase64String(GetTestDataFileContentsAsBytes(fileName));
        return $"data:{mimeType};base64,{content}";
    }

    private ConverseResponse CreateConverseResponse(string text, ConversationRole role)
    {
        return new ConverseResponse
        {
            Output = new ConverseOutput
            {
                Message = new Message
                {
                    Role = role,
                    Content = new List<ContentBlock> { new() { Text = text } }
                }
            },
            Metrics = new ConverseMetrics(),
            StopReason = StopReason.Max_tokens,
            Usage = new TokenUsage()
        };
    }
}
