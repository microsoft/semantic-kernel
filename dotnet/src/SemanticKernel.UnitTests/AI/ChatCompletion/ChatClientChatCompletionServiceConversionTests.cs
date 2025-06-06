// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

/// <summary>
/// Unit tests for ChatClientChatCompletionService conversion logic.
/// Tests verify that metadata and usage content are properly preserved when converting
/// from IChatClient abstractions to Semantic Kernel types.
/// </summary>
public sealed class ChatClientChatCompletionServiceConversionTests
{
    [Fact]
    public async Task GetChatMessageContentsAsyncWithUsageDetailsPreservesUsageInMetadata()
    {
        // Arrange
        using var chatClient = new TestChatClient
        {
            CompleteAsyncDelegate = (messages, options, cancellationToken) =>
            {
                return Task.FromResult(new ChatResponse([new ChatMessage(ChatRole.Assistant, "Test response")])
                {
                    Usage = new UsageDetails { InputTokenCount = 10, OutputTokenCount = 20, TotalTokenCount = 30 },
                    ModelId = "test-model",
                    RawRepresentation = "raw-response"
                });
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Test message");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.Single(result);
        var message = result[0];
        Assert.NotNull(message.Metadata);
        Assert.True(message.Metadata.ContainsKey("Usage"));
        var usageDetails = Assert.IsType<UsageDetails>(message.Metadata["Usage"]);
        Assert.Equal(10, usageDetails.InputTokenCount);
        Assert.Equal(20, usageDetails.OutputTokenCount);
        Assert.Equal(30, usageDetails.TotalTokenCount);
        Assert.Equal("test-model", message.ModelId);
        Assert.Equal("raw-response", message.InnerContent);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithoutUsageHasNullUsageInMetadata()
    {
        // Arrange
        using var chatClient = new TestChatClient
        {
            CompleteAsyncDelegate = (messages, options, cancellationToken) =>
            {
                return Task.FromResult(new ChatResponse([new ChatMessage(ChatRole.Assistant, "Test response")])
                {
                    Usage = null,
                    ModelId = "test-model"
                });
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Test message");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.Single(result);
        var message = result[0];
        Assert.NotNull(message.Metadata);
        Assert.True(message.Metadata.ContainsKey("Usage"));
        Assert.Null(message.Metadata["Usage"]);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithUsageContentPreservesUsageInMetadata()
    {
        // Arrange
        var expectedUsage = new UsageContent(new UsageDetails { InputTokenCount = 5, OutputTokenCount = 10, TotalTokenCount = 15 });
        using var chatClient = new TestChatClient
        {
            CompleteStreamingAsyncDelegate = (messages, options, cancellationToken) =>
            {
                return new[]
                {
                    new ChatResponseUpdate(ChatRole.Assistant, "Hello"),
                    new ChatResponseUpdate(ChatRole.Assistant, " World") { Contents = [expectedUsage] },
                    new ChatResponseUpdate(ChatRole.Assistant, "!") { ModelId = "test-model" }
                }.ToAsyncEnumerable();
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Test message");

        // Act
        var results = new List<StreamingChatMessageContent>();
        await foreach (var update in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            results.Add(update);
        }

        // Assert
        Assert.Equal(3, results.Count);

        // Check the update with usage content
        var usageUpdate = results[1];
        Assert.NotNull(usageUpdate.Metadata);
        Assert.True(usageUpdate.Metadata.ContainsKey("Usage"));
        Assert.Equal(expectedUsage, usageUpdate.Metadata["Usage"]);

        // Check model ID is preserved
        var modelUpdate = results[2];
        Assert.Equal("test-model", modelUpdate.ModelId);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithInnerContentPreservesInnerContent()
    {
        // Arrange
        using var chatClient = new TestChatClient
        {
            CompleteStreamingAsyncDelegate = (messages, options, cancellationToken) =>
            {
                return new[]
                {
                    new ChatResponseUpdate(ChatRole.Assistant, "Test")
                    {
                        RawRepresentation = "raw-stream-data",
                        ModelId = "test-model"
                    }
                }.ToAsyncEnumerable();
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Test message");

        // Act
        var results = new List<StreamingChatMessageContent>();
        await foreach (var update in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            results.Add(update);
        }

        // Assert
        Assert.Single(results);
        var message = results[0];
        Assert.Equal("raw-stream-data", message.InnerContent);
        Assert.Equal("test-model", message.ModelId);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithAdditionalPropertiesPreservesMetadata()
    {
        // Arrange
        var additionalProps = new AdditionalPropertiesDictionary
        {
            ["custom-key"] = "custom-value",
            ["another-key"] = 42
        };

        using var chatClient = new TestChatClient
        {
            CompleteAsyncDelegate = (messages, options, cancellationToken) =>
            {
                var message = new ChatMessage(ChatRole.Assistant, "Test response")
                {
                    AdditionalProperties = additionalProps
                };
                return Task.FromResult(new ChatResponse([message])
                {
                    Usage = new UsageDetails { InputTokenCount = 5, OutputTokenCount = 15, TotalTokenCount = 20 }
                });
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Test message");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.Single(result);
        var message = result[0];
        Assert.NotNull(message.Metadata);
        Assert.True(message.Metadata.ContainsKey("Usage"));
        var usageDetails = Assert.IsType<UsageDetails>(message.Metadata["Usage"]);
        Assert.Equal(5, usageDetails.InputTokenCount);
        Assert.Equal(15, usageDetails.OutputTokenCount);
        Assert.Equal(20, usageDetails.TotalTokenCount);
        Assert.True(message.Metadata.ContainsKey("custom-key"));
        Assert.Equal("custom-value", message.Metadata["custom-key"]);
        Assert.True(message.Metadata.ContainsKey("another-key"));
        Assert.Equal(42, message.Metadata["another-key"]);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithAdditionalPropertiesPreservesMetadata()
    {
        // Arrange
        var additionalProps = new AdditionalPropertiesDictionary
        {
            ["custom-key"] = "custom-value",
            ["stream-id"] = "stream-123"
        };

        using var chatClient = new TestChatClient
        {
            CompleteStreamingAsyncDelegate = (messages, options, cancellationToken) =>
            {
                return new[]
                {
                    new ChatResponseUpdate(ChatRole.Assistant, "Test")
                    {
                        AdditionalProperties = additionalProps,
                        RawRepresentation = "raw-stream-data"
                    }
                }.ToAsyncEnumerable();
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Test message");

        // Act
        var results = new List<StreamingChatMessageContent>();
        await foreach (var update in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            results.Add(update);
        }

        // Assert
        Assert.Single(results);
        var message = results[0];
        Assert.NotNull(message.Metadata);
        Assert.True(message.Metadata.ContainsKey("custom-key"));
        Assert.Equal("custom-value", message.Metadata["custom-key"]);
        Assert.True(message.Metadata.ContainsKey("stream-id"));
        Assert.Equal("stream-123", message.Metadata["stream-id"]);
        Assert.Equal("raw-stream-data", message.InnerContent);
    }

    [Fact]
    public async Task GetChatMessageContentsAsyncWithFunctionCallContentPreservesInnerContentAndMetadata()
    {
        // Arrange
        var functionCall = new Microsoft.Extensions.AI.FunctionCallContent("call-456", "WeatherFunction",
            new Dictionary<string, object?> { ["location"] = "Seattle", ["units"] = "metric" })
        {
            RawRepresentation = "function-call-raw"
        };

        using var chatClient = new TestChatClient
        {
            CompleteAsyncDelegate = (messages, options, cancellationToken) =>
            {
                var message = new ChatMessage(ChatRole.Assistant, [functionCall])
                {
                    RawRepresentation = "message-raw-content"
                };
                return Task.FromResult(new ChatResponse([message])
                {
                    Usage = new UsageDetails { InputTokenCount = 15, OutputTokenCount = 25, TotalTokenCount = 40 },
                    ModelId = "function-model",
                    RawRepresentation = "response-raw"
                });
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("What's the weather?");

        // Act
        var result = await service.GetChatMessageContentsAsync(chatHistory);

        // Assert
        Assert.Single(result);
        var message = result[0];
        Assert.Equal("response-raw", message.InnerContent);
        Assert.Equal("function-model", message.ModelId);
        Assert.NotNull(message.Metadata);
        Assert.True(message.Metadata.ContainsKey("Usage"));
        var usageDetails = Assert.IsType<UsageDetails>(message.Metadata["Usage"]);
        Assert.Equal(15, usageDetails.InputTokenCount);
        Assert.Equal(25, usageDetails.OutputTokenCount);
        Assert.Equal(40, usageDetails.TotalTokenCount);

        Assert.Single(message.Items);
        var functionCallContent = Assert.IsType<Microsoft.SemanticKernel.FunctionCallContent>(message.Items[0]);
        Assert.Equal("call-456", functionCallContent.Id);
        Assert.Equal("WeatherFunction", functionCallContent.FunctionName);
        Assert.Equal("function-call-raw", functionCallContent.InnerContent);
        Assert.Equal("function-model", functionCallContent.ModelId);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithFunctionCallsPreservesInnerContent()
    {
        // Arrange
        var functionCall = new Microsoft.Extensions.AI.FunctionCallContent("call-123", "TestFunction",
            new Dictionary<string, object?> { ["param"] = "value" })
        {
            RawRepresentation = "function-raw-data"
        };

        using var chatClient = new TestChatClient
        {
            CompleteStreamingAsyncDelegate = (messages, options, cancellationToken) =>
            {
                return new[]
                {
                    new ChatResponseUpdate(ChatRole.Assistant, [functionCall])
                    {
                        ModelId = "test-model",
                        RawRepresentation = "update-raw-data"
                    }
                }.ToAsyncEnumerable();
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Test message");

        // Act
        var results = new List<StreamingChatMessageContent>();
        await foreach (var update in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            results.Add(update);
        }

        // Assert
        Assert.Single(results);
        var message = results[0];
        Assert.Equal("update-raw-data", message.InnerContent);
        Assert.Equal("test-model", message.ModelId);
        Assert.Single(message.Items);

        var functionCallItem = Assert.IsType<Microsoft.SemanticKernel.StreamingFunctionCallUpdateContent>(message.Items[0]);
        Assert.Equal("call-123", functionCallItem.CallId);
        Assert.Equal("TestFunction", functionCallItem.Name);
        Assert.Equal("function-raw-data", functionCallItem.InnerContent);
        Assert.Equal("test-model", functionCallItem.ModelId);
    }

    [Fact]
    public async Task GetStreamingChatMessageContentsAsyncWithTextAndUsageContentCreatesCorrectStreamingContent()
    {
        // Arrange
        var expectedUsage = new UsageContent(new UsageDetails { InputTokenCount = 8, OutputTokenCount = 12, TotalTokenCount = 20 });
        var textContent = new Microsoft.Extensions.AI.TextContent("Hello World");

        using var chatClient = new TestChatClient
        {
            CompleteStreamingAsyncDelegate = (messages, options, cancellationToken) =>
            {
                return new[]
                {
                    new ChatResponseUpdate(ChatRole.Assistant, [textContent, expectedUsage])
                    {
                        ModelId = "test-model",
                        RawRepresentation = "combined-content-raw"
                    }
                }.ToAsyncEnumerable();
            }
        };

        var service = chatClient.AsChatCompletionService();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Test message");

        // Act
        var results = new List<StreamingChatMessageContent>();
        await foreach (var update in service.GetStreamingChatMessageContentsAsync(chatHistory))
        {
            results.Add(update);
        }

        // Assert
        Assert.Single(results);
        var message = results[0];

        // Should have only text content as streaming item, usage goes to metadata
        Assert.Single(message.Items);

        // Check text content
        var streamingTextContent = Assert.IsType<Microsoft.SemanticKernel.StreamingTextContent>(message.Items[0]);
        Assert.Equal("Hello World", streamingTextContent.Text);
        Assert.Equal("test-model", streamingTextContent.ModelId);

        // Check overall message metadata - usage content should be in metadata
        Assert.NotNull(message.Metadata);
        Assert.True(message.Metadata.ContainsKey("Usage"));
        Assert.Equal(expectedUsage, message.Metadata["Usage"]);
        Assert.Equal("combined-content-raw", message.InnerContent);
        Assert.Equal("test-model", message.ModelId);
    }

    /// <summary>
    /// Test implementation of IChatClient for unit testing.
    /// </summary>
    private sealed class TestChatClient : IChatClient
    {
        public Func<IEnumerable<ChatMessage>, ChatOptions?, CancellationToken, Task<ChatResponse>>? CompleteAsyncDelegate { get; set; }
        public Func<IEnumerable<ChatMessage>, ChatOptions?, CancellationToken, IAsyncEnumerable<ChatResponseUpdate>>? CompleteStreamingAsyncDelegate { get; set; }

        public ChatClientMetadata Metadata { get; set; } = new("TestChatClient", null, "test-model");

        public Task<ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            return this.CompleteAsyncDelegate?.Invoke(messages, options, cancellationToken)
                ?? throw new NotImplementedException("CompleteAsyncDelegate not set");
        }

        public IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            return this.CompleteStreamingAsyncDelegate?.Invoke(messages, options, cancellationToken)
                ?? throw new NotImplementedException("CompleteStreamingAsyncDelegate not set");
        }

        public TService? GetService<TService>(object? key = null) where TService : class
        {
            return typeof(TService) == typeof(ChatClientMetadata) ? (TService)(object)this.Metadata : null;
        }

        public object? GetService(Type serviceType, object? serviceKey = null)
        {
            return serviceType == typeof(ChatClientMetadata) ? this.Metadata : null;
        }

        public void Dispose() { }
    }
}
