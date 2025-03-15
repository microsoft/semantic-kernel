// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.OpenApi.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests.Client;

/// <summary>
/// Unit tests for <see cref="MistralClient"/>.
/// </summary>
public sealed class MistralClientTests : MistralTestBase
{
    [Fact]
    public void ValidateRequiredArguments()
    {
        // Arrange
        // Act
        // Assert
        Assert.Throws<ArgumentException>(() => new MistralClient(string.Empty, new HttpClient(), "key"));
        Assert.Throws<ArgumentException>(() => new MistralClient("model", new HttpClient(), string.Empty));
#pragma warning disable CS8625 // Cannot convert null literal to non-nullable reference type.
        Assert.Throws<ArgumentNullException>(() => new MistralClient(null, new HttpClient(), "key"));
        Assert.Throws<ArgumentNullException>(() => new MistralClient("model", null, "key"));
        Assert.Throws<ArgumentNullException>(() => new MistralClient("model", new HttpClient(), null));
#pragma warning restore CS8625 // Cannot convert null literal to non-nullable reference type.
    }

    [Fact]
    public void ValidateDeserializeChatCompletionMistralChatMessage()
    {
        var json = "{\"role\":\"assistant\",\"content\":\"Some response.\",\"tool_calls\":null}";

        MistralChatMessage? deserializedResponse = JsonSerializer.Deserialize<MistralChatMessage>(json);
        Assert.NotNull(deserializedResponse);
    }

    [Fact]
    public void ValidateDeserializeChatCompletionResponse()
    {
        var json = "{\"id\":\"aee5e73a5ef241be89cd7d3e9c45089a\",\"object\":\"chat.completion\",\"created\":1732882368,\"model\":\"mistral-large-latest\",\"choices\":[{\"index\":0,\"message\":{\"role\":\"assistant\",\"content\":\"Some response.\",\"tool_calls\":null},\"finish_reason\":\"stop\"}],\"usage\":{\"prompt_tokens\":17,\"total_tokens\":124,\"completion_tokens\":107}}";

        ChatCompletionResponse? deserializedResponse = JsonSerializer.Deserialize<ChatCompletionResponse>(json);
        Assert.NotNull(deserializedResponse);
    }

    [Fact]
    public async Task ValidateChatMessageRequestAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-small-latest", "https://api.mistral.ai/v1/chat/completions", "chat_completions_response.json");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { MaxTokens = 1024, Temperature = 0.9 };
        await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings);

        // Assert
        var request = this.DelegatingHandler!.RequestContent;
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Equal("mistral-small-latest", chatRequest.Model);
        Assert.Equal(1024, chatRequest.MaxTokens);
        Assert.Equal(0.9, chatRequest.Temperature);
        Assert.Single(chatRequest.Messages);
        Assert.Equal("user", chatRequest.Messages[0].Role);
        Assert.Equal("What is the best French cheese?", chatRequest.Messages[0].Content?.ToString());
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-tiny", "https://api.mistral.ai/v1/chat/completions", "chat_completions_response.json");

        // Act
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("I don't have a favorite condiment as I don't consume food or condiments. However, I can tell you that many people enjoy using ketchup, mayonnaise, hot sauce, soy sauce, or mustard as condiments to enhance the flavor of their meals. Some people also enjoy using herbs, spices, or vinegars as condiments. Ultimately, the best condiment is a matter of personal preference.", response[0].Content);
        Assert.Equal("mistral-tiny", response[0].ModelId);
        Assert.Equal(AuthorRole.Assistant, response[0].Role);
        Assert.NotNull(response[0].Metadata);
        Assert.Equal(7, response[0].Metadata?.Count);
    }

    [Fact]
    public async Task ValidateGenerateEmbeddingsAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-tiny", "https://api.mistral.ai/v1/embeddings", "embeddings_response.json");

        // Act
        List<string> data = ["Hello", "world"];
        var response = await client.GenerateEmbeddingsAsync(data, default);

        // Assert
        Assert.NotNull(response);
        Assert.Equal(2, response.Count);
        Assert.Equal(1024, response[0].Length);
        Assert.Equal(1024, response[1].Length);
    }

    [Fact]
    public async Task ValidateGetStreamingChatMessageContentsAsync()
    {
        // Arrange
        var client = this.CreateMistralClientStreaming("mistral-tiny", "https://api.mistral.ai/v1/chat/completions", "chat_completions_streaming_response.txt");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the best French cheese?")
        };

        // Act
        var response = client.GetStreamingChatMessageContentsAsync(chatHistory, default);
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in response)
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotNull(response);
        Assert.Equal(124, chunks.Count);
        foreach (var chunk in chunks)
        {
            Assert.NotNull(chunk);
            Assert.Equal("mistral-tiny", chunk.ModelId);
            Assert.NotNull(chunk.Content);
            Assert.NotNull(chunk.Role);
            Assert.NotNull(chunk.Metadata);
        }
    }

    [Fact]
    public async Task ValidateChatHistoryFirstSystemOrUserMessageAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-tiny", "https://api.mistral.ai/v1/chat/completions", "chat_completions_streaming_response.txt");

        // First message in chat history must be a user or system message
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.Assistant, "What is the best French cheese?")
        };

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => await client.GetChatMessageContentsAsync(chatHistory, default));
    }

    [Fact]
    public async Task ValidateEmptyChatHistoryAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-tiny", "https://api.mistral.ai/v1/chat/completions", "chat_completions_streaming_response.txt");
        var chatHistory = new ChatHistory();

        // Act & Assert
        await Assert.ThrowsAsync<ArgumentException>(async () => await client.GetChatMessageContentsAsync(chatHistory, default));
    }

    [Fact]
    public async Task ValidateChatMessageRequestWithToolsAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-tiny", "https://api.mistral.ai/v1/chat/completions", "function_call_response.json");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };

        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.EnableKernelFunctions };

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        var request = this.DelegatingHandler!.RequestContent;
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Null(chatRequest.DocumentPageLimit);
        Assert.Null(chatRequest.DocumentImageLimit);
        Assert.Equal("auto", chatRequest.ToolChoice);
        Assert.NotNull(chatRequest.Tools);
        Assert.Single(chatRequest.Tools);
        Assert.NotNull(chatRequest.Tools[0].Function.Parameters);
        Assert.Equal(["location"], chatRequest.Tools[0].Function.Parameters?.Required);
        Assert.Equal("string", chatRequest.Tools[0].Function.Parameters?.Properties["location"].RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public async Task ValidateGetStreamingChatMessageContentsWithToolsAsync()
    {
        // Arrange
        var client = this.CreateMistralClientStreaming("mistral-tiny", "https://api.mistral.ai/v1/chat/completions", "chat_completions_streaming_function_call_response.txt");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var response = client.GetStreamingChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);
        var chunks = new List<StreamingChatMessageContent>();
        await foreach (var chunk in response)
        {
            chunks.Add(chunk);
        }

        // Assert
        Assert.NotNull(response);
        Assert.Equal(12, chunks.Count); // Test will loop until maximum use attempts is reached
        var request = this.DelegatingHandler!.RequestContent;
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Equal("auto", chatRequest.ToolChoice);
        Assert.NotNull(chatRequest.Tools);
        Assert.Single(chatRequest.Tools);
        Assert.NotNull(chatRequest.Tools[0].Function.Parameters);
        Assert.Equal(["location"], chatRequest.Tools[0].Function.Parameters?.Required);
        Assert.Equal("string", chatRequest.Tools[0].Function.Parameters?.Properties["location"].RootElement.GetProperty("type").GetString());
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithFunctionCallAsync()
    {
        // Arrange
        var client = this.CreateMistralClient(
            "mistral-large-latest",
            "https://api.mistral.ai/v1/chat/completions",
            "chat_completions_function_call_response.json",
            "chat_completions_function_called_response.json");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("The weather in Paris is mostly cloudy with a temperature of 12°C. The wind speed is 11 KMPH and the humidity is at 48%.", response[0].Content);
        Assert.Equal("mistral-large-latest", response[0].ModelId);
        Assert.Equal(2, this.DelegatingHandler!.SendAsyncCallCount);
        Assert.Equal(3, chatHistory.Count);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithFunctionCallNoneAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-large-latest", "https://api.mistral.ai/v1/chat/completions", "chat_completions_function_call_none_response.json");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.NoKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("Sure, let me check the weather for you.\n\n[{\"name\": \"WeatherPlugin-GetWeather\", \"arguments\": {\"location\": \"Paris, 75\"}}}]", response[0].Content);
        Assert.Equal("mistral-large-latest", response[0].ModelId);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithFunctionCallRequiredAsync()
    {
        // Arrange
        var client = this.CreateMistralClient(
            "mistral-large-latest",
            "https://api.mistral.ai/v1/chat/completions",
            "chat_completions_function_call_response.json",
            "chat_completions_function_called_response.json");

        var kernel = new Kernel();
        var plugin = kernel.Plugins.AddFromType<WeatherPlugin>();

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.RequiredFunctions(plugin, true) };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("The weather in Paris is mostly cloudy with a temperature of 12°C. The wind speed is 11 KMPH and the humidity is at 48%.", response[0].Content);
        Assert.Equal("mistral-large-latest", response[0].ModelId);
        Assert.Equal(2, this.DelegatingHandler!.SendAsyncCallCount);
        Assert.Equal(3, chatHistory.Count);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithFunctionInvocationFilterAsync()
    {
        // Arrange
        var client = this.CreateMistralClient(
            "mistral-large-latest",
            "https://api.mistral.ai/v1/chat/completions",
            "chat_completions_function_call_response.json",
            "chat_completions_function_called_response.json");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        var invokedFunctions = new List<string>();
        var filter = new FakeFunctionFilter(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
        });
        kernel.FunctionInvocationFilters.Add(filter);

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("The weather in Paris is mostly cloudy with a temperature of 12°C. The wind speed is 11 KMPH and the humidity is at 48%.", response[0].Content);
        Assert.Equal("mistral-large-latest", response[0].ModelId);
        Assert.Equal(2, this.DelegatingHandler!.SendAsyncCallCount);
        Assert.Equal(3, chatHistory.Count);
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task FilterContextHasValidStreamingFlagAsync(bool isStreaming)
    {
        // Arrange
        bool? actualStreamingFlag = null;

        var client = isStreaming ?
            this.CreateMistralClientStreaming("mistral-tiny", "https://api.mistral.ai/v1/chat/completions", "chat_completions_streaming_function_call_response.txt") :
            this.CreateMistralClient("mistral-large-latest", "https://api.mistral.ai/v1/chat/completions", "chat_completions_function_call_response.json", "chat_completions_function_called_response.json");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        var filter = new FakeAutoFunctionFilter(async (context, next) =>
        {
            actualStreamingFlag = context.IsStreaming;
            await next(context);
        });

        kernel.AutoFunctionInvocationFilters.Add(filter);

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };

        if (isStreaming)
        {
            await client.GetStreamingChatMessageContentsAsync(chatHistory, default, executionSettings, kernel).ToListAsync();
        }
        else
        {
            await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);
        }

        // Assert
        Assert.Equal(isStreaming, actualStreamingFlag);
    }

    [Fact]
    public async Task ValidateGetChatMessageContentsWithAutoFunctionInvocationFilterTerminateAsync()
    {
        // Arrange
        var client = this.CreateMistralClient(
            "mistral-large-latest",
            "https://api.mistral.ai/v1/chat/completions",
            "chat_completions_function_call_response.json",
            "chat_completions_function_called_response.json");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        var invokedFunctions = new List<string>();
        var filter = new FakeAutoFunctionFilter(async (context, next) =>
        {
            invokedFunctions.Add(context.Function.Name);
            await next(context);
            context.Terminate = true;
        });
        kernel.AutoFunctionInvocationFilters.Add(filter);

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings, kernel);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Equal("12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy", response[0].Content);
        Assert.Null(response[0].ModelId);
        Assert.Equal(1, this.DelegatingHandler!.SendAsyncCallCount);
        Assert.Equal(3, chatHistory.Count);
        Assert.Contains("GetWeather", invokedFunctions);
    }

    [Fact]
    public async Task ValidateGetStreamingChatMessageContentWithAutoFunctionInvocationFilterTerminateAsync()
    {
        // Arrange
        var client = this.CreateMistralClientStreaming("mistral-tiny", "https://api.mistral.ai/v1/chat/completions", "chat_completions_streaming_function_call_response.txt");

        var kernel = new Kernel();
        kernel.Plugins.AddFromType<WeatherPlugin>();

        var filter = new FakeAutoFunctionFilter(async (context, next) =>
        {
            await next(context);
            context.Terminate = true;
        });
        kernel.AutoFunctionInvocationFilters.Add(filter);

        var executionSettings = new MistralAIPromptExecutionSettings { ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions };
        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(AuthorRole.User, "What is the weather like in Paris?")
        };

        List<StreamingKernelContent> streamingContent = [];

        // Act
        await foreach (var item in client.GetStreamingChatMessageContentsAsync(chatHistory, default, executionSettings, kernel))
        {
            streamingContent.Add(item);
        }

        // Assert
        // Results of function invoked before termination should be returned 
        Assert.Equal(3, streamingContent.Count);

        var lastMessageContent = streamingContent[^1] as StreamingChatMessageContent;
        Assert.NotNull(lastMessageContent);

        Assert.Equal("12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy", lastMessageContent.Content);
        Assert.Equal(AuthorRole.Tool, lastMessageContent.Role);
    }

    [Theory]
    [InlineData("system", "System Content")]
    [InlineData("user", "User Content")]
    [InlineData("assistant", "Assistant Content")]
    public void ValidateToMistralChatMessages(string roleLabel, string content)
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var chatMessage = new ChatMessageContent()
        {
            Role = new AuthorRole(roleLabel),
            Content = content,
        };

        // Act
        var messages = client.ToMistralChatMessages(chatMessage, default);

        // Assert
        Assert.NotNull(messages);
        Assert.Single(messages);
    }

    [Fact]
    public void ValidateToMistralChatMessagesWithMultipleContents()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var chatMessage = new ChatMessageContent()
        {
            Role = AuthorRole.User,
            Items =
                [
                new TextContent("What is the weather like in Paris?"),
                    new ImageContent(new Uri("https://tripfixers.com/wp-content/uploads/2019/11/eiffel-tower-with-snow.jpeg"))
                ],
        };

        // Act
        var messages = client.ToMistralChatMessages(chatMessage, default);

        // Assert
        Assert.NotNull(messages);
        Assert.Single(messages);
        Assert.IsType<List<ContentChunk>>(messages[0].Content);
    }

    [Fact]
    public void ValidateToMistralChatMessagesWithFunctionCallContent()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var content = new ChatMessageContent()
        {
            Role = AuthorRole.Assistant,
            Items = [new FunctionCallContent("GetWeather"), new FunctionCallContent("GetCurrentTime")],
        };

        // Act
        var messages = client.ToMistralChatMessages(content, default);

        // Assert
        Assert.NotNull(messages);
        Assert.Single(messages);
    }

    [Fact]
    public void ValidateToMistralChatMessagesWithFunctionResultContent()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var content = new ChatMessageContent()
        {
            Role = AuthorRole.Tool,
            Items = [new FunctionResultContent("12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy"), new FunctionResultContent("15:20:44")],
        };

        // Act
        var messages = client.ToMistralChatMessages(content, default);

        // Assert
        Assert.NotNull(messages);
        Assert.Equal(2, messages.Count);
    }

    [Fact]
    public void ValidateCloneMistralAIPromptExecutionSettings()
    {
        // Arrange
        var settings = new MistralAIPromptExecutionSettings
        {
            MaxTokens = 1024,
            Temperature = 0.9,
            TopP = 0.9,
            FrequencyPenalty = 0.9,
            PresencePenalty = 0.9,
            Stop = ["stop"],
            SafePrompt = true,
            RandomSeed = 123,
            ResponseFormat = new { format = "json" },
        };

        // Act
        var clonedSettings = settings.Clone();

        // Assert
        Assert.NotNull(clonedSettings);
        Assert.IsType<MistralAIPromptExecutionSettings>(clonedSettings);
        var clonedMistralAISettings = clonedSettings as MistralAIPromptExecutionSettings;
        Assert.Equal(settings.MaxTokens, clonedMistralAISettings!.MaxTokens);
        Assert.Equal(settings.Temperature, clonedMistralAISettings.Temperature);
        Assert.Equal(settings.TopP, clonedMistralAISettings.TopP);
        Assert.Equal(settings.FrequencyPenalty, clonedMistralAISettings.FrequencyPenalty);
        Assert.Equal(settings.PresencePenalty, clonedMistralAISettings.PresencePenalty);
        Assert.Equal(settings.Stop, clonedMistralAISettings.Stop);
        Assert.Equal(settings.SafePrompt, clonedMistralAISettings.SafePrompt);
        Assert.Equal(settings.RandomSeed, clonedMistralAISettings.RandomSeed);
        Assert.Equal(settings.ResponseFormat, clonedMistralAISettings.ResponseFormat);
    }

    [Fact]
    public void ToMistralChatMessagesWithArrayOfByteBinaryContentShouldThrow()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var chatMessage = new ChatMessageContent()
        {
            Role = AuthorRole.User,
            Items =
            [
                new BinaryContent(data: new byte[] { 1, 2, 3 }, mimeType: "application/pdf")
            ],
        };

        // Act
        // Assert
        Assert.Throws<NotSupportedException>(() => client.ToMistralChatMessages(chatMessage, default));
    }

    [Fact]
    public void ToMistralChatMessagesWithBase64BinaryContentShouldThrow()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var chatMessage = new ChatMessageContent()
        {
            Role = AuthorRole.User,
            Items =
            [
                new BinaryContent(dataUri: "data:application/pdf:base64,sdfghjyswedfghjjhertgiutdgbg")
            ],
        };

        // Act
        // Assert
        Assert.Throws<NotSupportedException>(() => client.ToMistralChatMessages(chatMessage, default));
    }

    [Fact]
    public void ValidateToMistralChatMessagesWithUrlBinaryContent()
    {
        // Arrange
        using var httpClient = new HttpClient();
        var client = new MistralClient("mistral-large-latest", httpClient, "key");
        var chatMessage = new ChatMessageContent()
        {
            Role = AuthorRole.User,
            Items =
            [
                new BinaryContent(new Uri("https://arxiv.org/pdf/1805.04770"))
            ],
        };

        // Act
        var message = client.ToMistralChatMessages(chatMessage, default);
        var contents = message[0].Content as List<ContentChunk>;
        var content = contents![0] as DocumentUrlChunk;

        // Assert
        Assert.NotNull(message);
        Assert.Single(message);
        Assert.IsType<MistralChatMessage>(message[0]);
        Assert.Equal("user", message[0].Role);

        Assert.IsType<List<ContentChunk>>(message[0].Content);
        Assert.NotNull(contents);
        Assert.Single(contents);

        Assert.IsType<DocumentUrlChunk>(content);
        Assert.NotNull(content);
        Assert.Equal("https://arxiv.org/pdf/1805.04770", content.DocumentUrl);
        Assert.Equal("document_url", content.Type);
    }

    [Fact]
    public async Task ValidateToMistralChatMessagesWithDocumentRequestAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-small-latest", "https://api.mistral.ai/v1/chat/completions", "chat_completions_response_with_document.json");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(
                AuthorRole.User,
                [
                    new TextContent("Summarize the document for me."),
                    new BinaryContent(new Uri("https://arxiv.org/pdf/1805.04770"))
                ]),
        };

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { DocumentPageLimit = 64, DocumentImageLimit = 8 };
        await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings);
        var request = this.DelegatingHandler!.RequestContent;

        // Assert
        Assert.NotNull(request);
        var chatRequest = JsonSerializer.Deserialize<ChatCompletionRequest>(request);
        Assert.NotNull(chatRequest);
        Assert.Equal("mistral-small-latest", chatRequest.Model);
        Assert.Single(chatRequest.Messages);
        Assert.Equal("user", chatRequest.Messages[0].Role);
        Assert.NotNull(chatRequest.Messages[0].Content);
        Assert.Equal(64, chatRequest.DocumentPageLimit);
        Assert.Equal(8, chatRequest.DocumentImageLimit);

        // Assert
        var content = JsonSerializer.Serialize(chatRequest.Messages[0].Content);
        string json = """[{"text":"Summarize the document for me.","type":"text"},{"document_url":"https://arxiv.org/pdf/1805.04770","type":"document_url"}]""";
        Assert.Equal(json, content);
    }

    [Fact]
    public async Task ValidateToMistralChatMessagesWithDocumentResponseAsync()
    {
        // Arrange
        var client = this.CreateMistralClient("mistral-small-latest", "https://api.mistral.ai/v1/chat/completions", "chat_completions_response_with_document.json");

        var chatHistory = new ChatHistory
        {
            new ChatMessageContent(
                AuthorRole.User,
                [
                    new TextContent("Summarize the document for me."),
                    new BinaryContent(new Uri("https://arxiv.org/pdf/1805.04770"))
                ]),
        };

        // Act
        var executionSettings = new MistralAIPromptExecutionSettings { DocumentPageLimit = 64, DocumentImageLimit = 8 };
        var response = await client.GetChatMessageContentsAsync(chatHistory, default, executionSettings);

        // Assert
        Assert.NotNull(response);
        Assert.Single(response);
        Assert.Contains("The document titled \"Born-Again Neural Networks\"", response[0].Content);
        Assert.Equal("mistral-small-latest", response[0].ModelId);
        Assert.Equal(AuthorRole.Assistant, response[0].Role);
        Assert.NotNull(response[0].Metadata);
        Assert.Equal(7, response[0].Metadata?.Count);
        Assert.NotNull(response[0].Metadata?["Usage"]);
        Assert.NotNull(response[0].InnerContent);
        Assert.IsType<MistralChatChoice>(response[0].InnerContent);
    }

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Get the current weather in a given location.")]
        public string GetWeather(
            [Description("The city and department, e.g. Marseille, 13")] string location
        ) => "12°C\nWind: 11 KMPH\nHumidity: 48%\nMostly cloudy";
    }

    internal enum TemperatureUnit { Celsius, Fahrenheit }

    public class WidgetFactory
    {
        [KernelFunction]
        [Description("Creates a new widget of the specified type and colors")]
        public string CreateWidget([Description("The colors of the widget to be created")] WidgetColor[] widgetColors)
        {
            var colors = string.Join('-', widgetColors.Select(c => c.GetDisplayName()).ToArray());
            return $"Widget created with colors: {colors}";
        }
    }

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum WidgetColor
    {
        [Description("Use when creating a red item.")]
        Red,

        [Description("Use when creating a green item.")]
        Green,

        [Description("Use when creating a blue item.")]
        Blue
    }

    private sealed class FakeFunctionFilter(
        Func<FunctionInvocationContext, Func<FunctionInvocationContext, Task>, Task>? onFunctionInvocation = null) : IFunctionInvocationFilter
    {
        private readonly Func<FunctionInvocationContext, Func<FunctionInvocationContext, Task>, Task>? _onFunctionInvocation = onFunctionInvocation;

        public Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next) =>
            this._onFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }

    private sealed class FakeAutoFunctionFilter(
        Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? onAutoFunctionInvocation = null) : IAutoFunctionInvocationFilter
    {
        private readonly Func<AutoFunctionInvocationContext, Func<AutoFunctionInvocationContext, Task>, Task>? _onAutoFunctionInvocation = onAutoFunctionInvocation;

        public Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next) =>
            this._onAutoFunctionInvocation?.Invoke(context, next) ?? Task.CompletedTask;
    }

    private MistralClient CreateMistralClient(string modelId, string requestUri, params string[] responseData)
    {
        var responses = responseData.Select(this.GetTestResponseAsString).ToArray();
        this.DelegatingHandler = new AssertingDelegatingHandler(requestUri, responses);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient(modelId, this.HttpClient, "key");
        return client;
    }

    private MistralClient CreateMistralClientStreaming(string modelId, string requestUri, params string[] responseData)
    {
        var responses = responseData.Select(this.GetTestResponseAsBytes).ToArray();
        this.DelegatingHandler = new AssertingDelegatingHandler(requestUri, true, responses);
        this.HttpClient = new HttpClient(this.DelegatingHandler, false);
        var client = new MistralClient(modelId, this.HttpClient, "key");
        return client;
    }
}
