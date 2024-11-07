﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.UnitTests.AI;

public class ServiceConversionExtensionsTests
{
    [Fact]
    public void InvalidArgumentsThrow()
    {
        Assert.Throws<ArgumentNullException>("service", () => EmbeddingGenerationExtensions.AsEmbeddingGenerator<string, float>(null!));
        Assert.Throws<ArgumentNullException>("generator", () => EmbeddingGenerationExtensions.AsEmbeddingGenerationService<string, float>(null!));

        Assert.Throws<ArgumentNullException>("service", () => ChatCompletionServiceExtensions.AsChatClient(null!));
        Assert.Throws<ArgumentNullException>("client", () => ChatCompletionServiceExtensions.AsChatCompletionService(null!));
    }

    [Fact]
    public void AsEmbeddingGeneratorMetadataReturnsExpectedData()
    {
        IEmbeddingGenerator<string, Embedding<float>> generator = new TestEmbeddingGenerationService()
        {
            Attributes = new Dictionary<string, object?>
            {
                [AIServiceExtensions.ModelIdKey] = "examplemodel",
                [AIServiceExtensions.EndpointKey] = "https://example.com",
            }
        }.AsEmbeddingGenerator();

        Assert.NotNull(generator);
        Assert.NotNull(generator.Metadata);
        Assert.Equal(nameof(TestEmbeddingGenerationService), generator.Metadata.ProviderName);
        Assert.Equal("examplemodel", generator.Metadata.ModelId);
        Assert.Equal("https://example.com/", generator.Metadata.ProviderUri?.ToString());
    }

    [Fact]
    public void AsEmbeddingGenerationServiceReturnsExpectedAttributes()
    {
        using var generator = new TestEmbeddingGenerator()
        {
            Metadata = new EmbeddingGeneratorMetadata("exampleprovider", new Uri("https://example.com"), "examplemodel")
        };

        IEmbeddingGenerationService<string, float> service = generator.AsEmbeddingGenerationService();
        Assert.NotNull(service);
        Assert.NotNull(service.Attributes);
        Assert.Equal("https://example.com/", service.Attributes[AIServiceExtensions.EndpointKey]);
        Assert.Equal("examplemodel", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void AsChatClientMetadataReturnsExpectedData()
    {
        IChatClient client = new TestChatCompletionService()
        {
            Attributes = new Dictionary<string, object?>
            {
                [AIServiceExtensions.ModelIdKey] = "examplemodel",
                [AIServiceExtensions.EndpointKey] = "https://example.com",
            }
        }.AsChatClient();

        Assert.NotNull(client);
        Assert.NotNull(client.Metadata);
        Assert.Equal(nameof(TestChatCompletionService), client.Metadata.ProviderName);
        Assert.Equal("examplemodel", client.Metadata.ModelId);
        Assert.Equal("https://example.com/", client.Metadata.ProviderUri?.ToString());
    }

    [Fact]
    public void AsChatCompletionServiceReturnsExpectedAttributes()
    {
        using var client = new TestChatClient()
        {
            Metadata = new ChatClientMetadata("exampleprovider", new Uri("https://example.com"), "examplemodel")
        };

        IChatCompletionService service = client.AsChatCompletionService();
        Assert.NotNull(service);
        Assert.NotNull(service.Attributes);
        Assert.Equal("https://example.com/", service.Attributes[AIServiceExtensions.EndpointKey]);
        Assert.Equal("examplemodel", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public async Task AsEmbeddingGeneratorConvertedAsExpected()
    {
        IEmbeddingGenerator<string, Embedding<float>> generator = new TestEmbeddingGenerationService()
        {
            GenerateEmbeddingsAsyncDelegate = async (data, kernel, cancellationToken) =>
            {
                Assert.Single(data);
                Assert.Equal("some text", data.First());
                await Task.Yield();
                return [new float[] { 1, 2, 3 }];
            },
        }.AsEmbeddingGenerator();

        ReadOnlyMemory<float> embedding = await generator.GenerateEmbeddingVectorAsync("some text");
        Assert.Equal([1f, 2f, 3f], embedding.ToArray());
    }

    [Fact]
    public async Task AsEmbeddingGenerationServiceConvertedAsExpected()
    {
        using IEmbeddingGenerator<string, Embedding<float>> generator = new TestEmbeddingGenerator()
        {
            GenerateAsyncDelegate = async (values, options, cancellationToken) =>
            {
                Assert.Single(values);
                Assert.Equal("some text", values.First());
                await Task.Yield();
                return [new Embedding<float>(new float[] { 1, 2, 3 })];
            },
        };

        IEmbeddingGenerationService<string, float> service = generator.AsEmbeddingGenerationService();

        ReadOnlyMemory<float> embedding = await service.GenerateEmbeddingAsync("some text");
        Assert.Equal([1f, 2f, 3f], embedding.ToArray());
    }

    [Fact]
    public async Task AsChatClientNonStreamingContentConvertedAsExpected()
    {
        ChatHistory? actualChatHistory = null;
        PromptExecutionSettings? actualSettings = null;

        IChatClient client = new TestChatCompletionService()
        {
            GetChatMessageContentsAsyncDelegate = async (chatHistory, executionSettings, kernel, cancellationToken) =>
            {
                await Task.Yield();
                actualChatHistory = chatHistory;
                actualSettings = executionSettings;
                return [new ChatMessageContent() { Content = "the result" }];
            },
        }.AsChatClient();

        Microsoft.Extensions.AI.ChatCompletion result = await client.CompleteAsync([
            new(ChatRole.System,
            [
                new Microsoft.Extensions.AI.TextContent("some text"),
                new Microsoft.Extensions.AI.ImageContent("http://imageurl"),
            ]),
            new(ChatRole.User,
            [
                new Microsoft.Extensions.AI.AudioContent("http://audiourl"),
                new Microsoft.Extensions.AI.TextContent("some other text"),
            ]),
            new(ChatRole.Assistant,
            [
                new Microsoft.Extensions.AI.FunctionCallContent("call123", "FunctionName", new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }),
            ]),
            new(ChatRole.Tool,
            [
                new Microsoft.Extensions.AI.FunctionResultContent("call123", "FunctionName", 42),
            ]),
        ], new ChatOptions()
        {
            Temperature = 0.2f,
            MaxOutputTokens = 128,
            FrequencyPenalty = 0.5f,
            StopSequences = ["hello"],
            ModelId = "examplemodel",
            PresencePenalty = 0.3f,
            TopP = 0.75f,
            TopK = 50,
            ResponseFormat = ChatResponseFormat.Json,
        });

        Assert.NotNull(result);
        Assert.Equal("the result", result.Message.Text);

        Assert.NotNull(actualChatHistory);
        Assert.Equal(4, actualChatHistory.Count);

        Assert.Equal(AuthorRole.System, actualChatHistory[0].Role);
        Assert.Equal(AuthorRole.User, actualChatHistory[1].Role);
        Assert.Equal(AuthorRole.Assistant, actualChatHistory[2].Role);
        Assert.Equal(AuthorRole.Tool, actualChatHistory[3].Role);

        Assert.Equal(2, actualChatHistory[0].Items.Count);
        Assert.Equal(2, actualChatHistory[1].Items.Count);
        Assert.Single(actualChatHistory[2].Items);
        Assert.Single(actualChatHistory[3].Items);

        Assert.Equal("some text", Assert.IsType<Microsoft.SemanticKernel.TextContent>(actualChatHistory[0].Items[0]).Text);
        Assert.Equal("http://imageurl/", Assert.IsType<Microsoft.SemanticKernel.ImageContent>(actualChatHistory[0].Items[1]).Uri?.ToString());
        Assert.Equal("http://audiourl/", Assert.IsType<Microsoft.SemanticKernel.AudioContent>(actualChatHistory[1].Items[0]).Uri?.ToString());
        Assert.Equal("some other text", Assert.IsType<Microsoft.SemanticKernel.TextContent>(actualChatHistory[1].Items[1]).Text);

        var fcc = Assert.IsType<Microsoft.SemanticKernel.FunctionCallContent>(actualChatHistory[2].Items[0]);
        Assert.Equal("call123", fcc.Id);
        Assert.Equal("FunctionName", fcc.FunctionName);
        Assert.Equal(new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }, fcc.Arguments);

        var frc = Assert.IsType<Microsoft.SemanticKernel.FunctionResultContent>(actualChatHistory[3].Items[0]);
        Assert.Equal("call123", frc.CallId);
        Assert.Equal("FunctionName", frc.FunctionName);
        Assert.Equal(42, frc.Result);

        Assert.NotNull(actualSettings);
        Assert.Equal("examplemodel", actualSettings.ModelId);
        Assert.Equal(0.2f, actualSettings.ExtensionData?["temperature"]);
        Assert.Equal(128, actualSettings.ExtensionData?["max_tokens"]);
        Assert.Equal(0.5f, actualSettings.ExtensionData?["frequency_penalty"]);
        Assert.Equal(0.3f, actualSettings.ExtensionData?["presence_penalty"]);
        Assert.Equal(0.75f, actualSettings.ExtensionData?["top_p"]);
        Assert.Equal(50, actualSettings.ExtensionData?["top_k"]);
        Assert.Equal(new[] { "hello" }, actualSettings.ExtensionData?["stop_sequences"]);
        Assert.Equal("json_object", actualSettings.ExtensionData?["response_format"]);
    }

    [Fact]
    public async Task AsChatClientNonStreamingResponseFormatHandled()
    {
        PromptExecutionSettings? actualSettings = null;
        OpenAIPromptExecutionSettings? oaiSettings;

        IChatClient client = new TestChatCompletionService()
        {
            GetChatMessageContentsAsyncDelegate = async (chatHistory, executionSettings, kernel, cancellationToken) =>
            {
                await Task.Yield();
                actualSettings = executionSettings;
                return [new ChatMessageContent() { Content = "the result" }];
            },
        }.AsChatClient();

        List<ChatMessage> messages = [new(ChatRole.User, "hi")];

        await client.CompleteAsync(messages);
        oaiSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(JsonSerializer.Serialize(actualSettings));
        Assert.Null(oaiSettings);

        await client.CompleteAsync(messages, new() { ResponseFormat = ChatResponseFormat.Text });
        oaiSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(JsonSerializer.Serialize(actualSettings));
        Assert.Equal("text", oaiSettings?.ResponseFormat?.ToString());

        await client.CompleteAsync(messages, new() { ResponseFormat = ChatResponseFormat.Json });
        oaiSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(JsonSerializer.Serialize(actualSettings));
        Assert.Equal("json_object", oaiSettings?.ResponseFormat?.ToString());

        await client.CompleteAsync(messages, new() { ResponseFormat = ChatResponseFormat.ForJsonSchema("""
            {"type": "string"}
            """) });
        oaiSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(JsonSerializer.Serialize(actualSettings));
        Assert.Equal(JsonValueKind.Object, Assert.IsType<JsonElement>(oaiSettings?.ResponseFormat).ValueKind);
    }

    public static IEnumerable<object[]> AsChatClientNonStreamingToolsPropagatedMemberData()
    {
        yield return new object[] { null! };
        yield return new object[] { ChatToolMode.Auto };
        yield return new object[] { ChatToolMode.RequireAny };
        yield return new object[] { ChatToolMode.RequireSpecific("AIFunc2") };
    }

    [Theory]
    [MemberData(nameof(AsChatClientNonStreamingToolsPropagatedMemberData))]
    public async Task AsChatClientNonStreamingToolsPropagated(ChatToolMode mode)
    {
        PromptExecutionSettings? actualSettings = null;

        IChatClient client = new TestChatCompletionService()
        {
            GetChatMessageContentsAsyncDelegate = async (chatHistory, executionSettings, kernel, cancellationToken) =>
            {
                await Task.Yield();
                actualSettings = executionSettings;
                return [new ChatMessageContent() { Content = "the result" }];
            },
        }.AsChatClient();

        List<ChatMessage> messages = [new(ChatRole.User, "hi")];

        await client.CompleteAsync(messages, new()
        {
            Tools = [new NopAIFunction("AIFunc1"), new NopAIFunction("AIFunc2")],
            ToolMode = mode,
        });

        Assert.NotNull(actualSettings);
        var config = actualSettings.FunctionChoiceBehavior?.GetConfiguration(new FunctionChoiceBehaviorConfigurationContext([]));
        Assert.NotNull(config);
        Assert.NotNull(config.Functions);
        Assert.False(config.AutoInvoke);

        switch (mode)
        {
            case null:
            case AutoChatToolMode:
                Assert.Equal(FunctionChoice.Auto, config.Choice);
                Assert.Equal(2, config.Functions?.Count);
                Assert.Equal("AIFunc1", config.Functions?[0].Name);
                Assert.Equal("AIFunc2", config.Functions?[1].Name);
                break;

            case RequiredChatToolMode r:
                Assert.Equal(FunctionChoice.Required, config.Choice);
                if (r.RequiredFunctionName is null)
                {
                    Assert.Equal(2, config.Functions?.Count);
                    Assert.Equal("AIFunc1", config.Functions?[0].Name);
                    Assert.Equal("AIFunc2", config.Functions?[1].Name);
                }
                else
                {
                    Assert.Equal(1, config.Functions?.Count);
                    Assert.Equal("AIFunc2", config.Functions?[0].Name);
                }
                break;
        }

        foreach (var f in config.Functions!)
        {
            await Assert.ThrowsAsync<NotSupportedException>(async () => await f.InvokeAsync(new())!);
        }
    }

    private sealed class NopAIFunction(string name) : AIFunction
    {
        public override AIFunctionMetadata Metadata => new(name);

        protected override Task<object?> InvokeCoreAsync(IEnumerable<KeyValuePair<string, object?>> arguments, CancellationToken cancellationToken)
        {
            throw new FormatException();
        }
    }

    [Fact]
    public async Task AsChatClientStreamingContentConvertedAsExpected()
    {
        ChatHistory? actualChatHistory = null;
        PromptExecutionSettings? actualSettings = null;

        IChatClient client = new TestChatCompletionService()
        {
            GetStreamingChatMessageContentsAsyncDelegate = (chatHistory, executionSettings, kernel, cancellationToken) =>
            {
                actualChatHistory = chatHistory;
                actualSettings = executionSettings;
                return new List<StreamingChatMessageContent>()
                {
                    new(AuthorRole.Assistant, "the result"),
                }.ToAsyncEnumerable();
            },
        }.AsChatClient();

        List<StreamingChatCompletionUpdate> result = await client.CompleteStreamingAsync([
            new(ChatRole.System,
            [
                new Microsoft.Extensions.AI.TextContent("some text"),
                new Microsoft.Extensions.AI.ImageContent("http://imageurl"),
            ]),
            new(ChatRole.User,
            [
                new Microsoft.Extensions.AI.AudioContent("http://audiourl"),
                new Microsoft.Extensions.AI.TextContent("some other text"),
            ]),
            new(ChatRole.Assistant,
            [
                new Microsoft.Extensions.AI.FunctionCallContent("call123", "FunctionName", new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }),
            ]),
            new(ChatRole.Tool,
            [
                new Microsoft.Extensions.AI.FunctionResultContent("call123", "FunctionName", 42),
            ]),
        ], new ChatOptions()
        {
            Temperature = 0.2f,
            MaxOutputTokens = 128,
            FrequencyPenalty = 0.5f,
            StopSequences = ["hello"],
            ModelId = "examplemodel",
            PresencePenalty = 0.3f,
            TopP = 0.75f,
            TopK = 50,
            ResponseFormat = ChatResponseFormat.Json,
        }).ToListAsync();

        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal("the result", result.First().Text);

        Assert.NotNull(actualChatHistory);
        Assert.Equal(4, actualChatHistory.Count);

        Assert.Equal(AuthorRole.System, actualChatHistory[0].Role);
        Assert.Equal(AuthorRole.User, actualChatHistory[1].Role);
        Assert.Equal(AuthorRole.Assistant, actualChatHistory[2].Role);
        Assert.Equal(AuthorRole.Tool, actualChatHistory[3].Role);

        Assert.Equal(2, actualChatHistory[0].Items.Count);
        Assert.Equal(2, actualChatHistory[1].Items.Count);
        Assert.Single(actualChatHistory[2].Items);
        Assert.Single(actualChatHistory[3].Items);

        Assert.Equal("some text", Assert.IsType<Microsoft.SemanticKernel.TextContent>(actualChatHistory[0].Items[0]).Text);
        Assert.Equal("http://imageurl/", Assert.IsType<Microsoft.SemanticKernel.ImageContent>(actualChatHistory[0].Items[1]).Uri?.ToString());
        Assert.Equal("http://audiourl/", Assert.IsType<Microsoft.SemanticKernel.AudioContent>(actualChatHistory[1].Items[0]).Uri?.ToString());
        Assert.Equal("some other text", Assert.IsType<Microsoft.SemanticKernel.TextContent>(actualChatHistory[1].Items[1]).Text);

        var fcc = Assert.IsType<Microsoft.SemanticKernel.FunctionCallContent>(actualChatHistory[2].Items[0]);
        Assert.Equal("call123", fcc.Id);
        Assert.Equal("FunctionName", fcc.FunctionName);
        Assert.Equal(new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }, fcc.Arguments);

        var frc = Assert.IsType<Microsoft.SemanticKernel.FunctionResultContent>(actualChatHistory[3].Items[0]);
        Assert.Equal("call123", frc.CallId);
        Assert.Equal("FunctionName", frc.FunctionName);
        Assert.Equal(42, frc.Result);

        Assert.NotNull(actualSettings);
        Assert.Equal("examplemodel", actualSettings.ModelId);
        Assert.Equal(0.2f, actualSettings.ExtensionData?["temperature"]);
        Assert.Equal(128, actualSettings.ExtensionData?["max_tokens"]);
        Assert.Equal(0.5f, actualSettings.ExtensionData?["frequency_penalty"]);
        Assert.Equal(0.3f, actualSettings.ExtensionData?["presence_penalty"]);
        Assert.Equal(0.75f, actualSettings.ExtensionData?["top_p"]);
        Assert.Equal(50, actualSettings.ExtensionData?["top_k"]);
        Assert.Equal(new[] { "hello" }, actualSettings.ExtensionData?["stop_sequences"]);
        Assert.Equal("json_object", actualSettings.ExtensionData?["response_format"]);
    }

    [Fact]
    public async Task AsChatCompletionServiceNonStreamingContentConvertedAsExpected()
    {
        IList<ChatMessage>? actualChatHistory = null;
        ChatOptions? actualOptions = null;

        using IChatClient client = new TestChatClient()
        {
            CompleteAsyncDelegate = async (messages, options, cancellationToken) =>
            {
                await Task.Yield();
                actualChatHistory = messages;
                actualOptions = options;
                return new Microsoft.Extensions.AI.ChatCompletion(new ChatMessage() { Text = "the result" });
            },
        };

        IChatCompletionService service = client.AsChatCompletionService();

        ChatMessageContent result = await service.GetChatMessageContentAsync([
            new ChatMessageContent(AuthorRole.System,
            [
                new Microsoft.SemanticKernel.TextContent("some text"),
                new Microsoft.SemanticKernel.ImageContent(new Uri("http://imageurl")),
            ]),
            new ChatMessageContent(AuthorRole.User,
            [
                new Microsoft.SemanticKernel.AudioContent(new Uri("http://audiourl")),
                new Microsoft.SemanticKernel.TextContent("some other text"),
            ]),
            new ChatMessageContent(AuthorRole.Assistant,
            [
                new Microsoft.SemanticKernel.FunctionCallContent(id: "call123", functionName: "FunctionName", arguments: new() { ["key1"] = "value1", ["key2"] = "value2" }),
            ]),
            new ChatMessageContent(AuthorRole.Tool,
            [
                new Microsoft.SemanticKernel.FunctionResultContent(callId: "call123", functionName: "FunctionName", result: 42),
            ]),
        ], new OpenAIPromptExecutionSettings()
        {
            Temperature = 0.2f,
            MaxTokens = 128,
            FrequencyPenalty = 0.5f,
            StopSequences = ["hello"],
            ModelId = "examplemodel",
            Seed = 42,
            TopP = 0.75f,
            User = "user123",
        });

        Assert.NotNull(result);
        Assert.Equal("the result", result.Content);

        Assert.NotNull(actualChatHistory);
        Assert.Equal(4, actualChatHistory.Count);

        Assert.Equal(ChatRole.System, actualChatHistory[0].Role);
        Assert.Equal(ChatRole.User, actualChatHistory[1].Role);
        Assert.Equal(ChatRole.Assistant, actualChatHistory[2].Role);
        Assert.Equal(ChatRole.Tool, actualChatHistory[3].Role);

        Assert.Equal(2, actualChatHistory[0].Contents.Count);
        Assert.Equal(2, actualChatHistory[1].Contents.Count);
        Assert.Single(actualChatHistory[2].Contents);
        Assert.Single(actualChatHistory[3].Contents);

        Assert.Equal("some text", Assert.IsType<Microsoft.Extensions.AI.TextContent>(actualChatHistory[0].Contents[0]).Text);
        Assert.Equal("http://imageurl/", Assert.IsType<Microsoft.Extensions.AI.ImageContent>(actualChatHistory[0].Contents[1]).Uri?.ToString());
        Assert.Equal("http://audiourl/", Assert.IsType<Microsoft.Extensions.AI.AudioContent>(actualChatHistory[1].Contents[0]).Uri?.ToString());
        Assert.Equal("some other text", Assert.IsType<Microsoft.Extensions.AI.TextContent>(actualChatHistory[1].Contents[1]).Text);

        var fcc = Assert.IsType<Microsoft.Extensions.AI.FunctionCallContent>(actualChatHistory[2].Contents[0]);
        Assert.Equal("call123", fcc.CallId);
        Assert.Equal("FunctionName", fcc.Name);
        Assert.Equal(new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }, fcc.Arguments);

        var frc = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(actualChatHistory[3].Contents[0]);
        Assert.Equal("call123", frc.CallId);
        Assert.Equal("FunctionName", frc.Name);
        Assert.Equal(42, frc.Result);

        Assert.NotNull(actualOptions);
        Assert.Equal("examplemodel", actualOptions.ModelId);
        Assert.Equal(0.2f, actualOptions.Temperature);
        Assert.Equal(128, actualOptions.MaxOutputTokens);
        Assert.Equal(0.5f, actualOptions.FrequencyPenalty);
        Assert.Equal(0.75f, actualOptions.TopP);
        Assert.Equal(["hello"], actualOptions.StopSequences);
        Assert.Equal(42, actualOptions.AdditionalProperties?.TryGetValue("Seed", out int seed) is true ? seed : 0);
        Assert.Equal("user123", actualOptions.AdditionalProperties?["User"]);
    }

    [Fact]
    public async Task AsChatCompletionServiceStreamingContentConvertedAsExpected()
    {
        IList<ChatMessage>? actualChatHistory = null;
        ChatOptions? actualOptions = null;

        using IChatClient client = new TestChatClient()
        {
            CompleteStreamingAsyncDelegate = (messages, options, cancellationToken) =>
            {
                actualChatHistory = messages;
                actualOptions = options;
                return new List<StreamingChatCompletionUpdate>()
                {
                    new() { Role = ChatRole.Assistant, Text = "the result" }
                }.ToAsyncEnumerable();
            },
        };

        IChatCompletionService service = client.AsChatCompletionService();

        var result = await service.GetStreamingChatMessageContentsAsync([
            new ChatMessageContent(AuthorRole.System,
            [
                new Microsoft.SemanticKernel.TextContent("some text"),
                new Microsoft.SemanticKernel.ImageContent(new Uri("http://imageurl")),
            ]),
            new ChatMessageContent(AuthorRole.User,
            [
                new Microsoft.SemanticKernel.AudioContent(new Uri("http://audiourl")),
                new Microsoft.SemanticKernel.TextContent("some other text"),
            ]),
            new ChatMessageContent(AuthorRole.Assistant,
            [
                new Microsoft.SemanticKernel.FunctionCallContent(id: "call123", functionName: "FunctionName", arguments: new() { ["key1"] = "value1", ["key2"] = "value2" }),
            ]),
            new ChatMessageContent(AuthorRole.Tool,
            [
                new Microsoft.SemanticKernel.FunctionResultContent(callId: "call123", functionName: "FunctionName", result: 42),
            ]),
        ], new OpenAIPromptExecutionSettings()
        {
            Temperature = 0.2f,
            MaxTokens = 128,
            FrequencyPenalty = 0.5f,
            StopSequences = ["hello"],
            ModelId = "examplemodel",
            Seed = 42,
            TopP = 0.75f,
            User = "user123",
        }).ToListAsync();

        Assert.NotNull(result);
        Assert.Single(result);
        Assert.Equal("the result", result.First().Content);

        Assert.NotNull(actualChatHistory);
        Assert.Equal(4, actualChatHistory.Count);

        Assert.Equal(ChatRole.System, actualChatHistory[0].Role);
        Assert.Equal(ChatRole.User, actualChatHistory[1].Role);
        Assert.Equal(ChatRole.Assistant, actualChatHistory[2].Role);
        Assert.Equal(ChatRole.Tool, actualChatHistory[3].Role);

        Assert.Equal(2, actualChatHistory[0].Contents.Count);
        Assert.Equal(2, actualChatHistory[1].Contents.Count);
        Assert.Single(actualChatHistory[2].Contents);
        Assert.Single(actualChatHistory[3].Contents);

        Assert.Equal("some text", Assert.IsType<Microsoft.Extensions.AI.TextContent>(actualChatHistory[0].Contents[0]).Text);
        Assert.Equal("http://imageurl/", Assert.IsType<Microsoft.Extensions.AI.ImageContent>(actualChatHistory[0].Contents[1]).Uri?.ToString());
        Assert.Equal("http://audiourl/", Assert.IsType<Microsoft.Extensions.AI.AudioContent>(actualChatHistory[1].Contents[0]).Uri?.ToString());
        Assert.Equal("some other text", Assert.IsType<Microsoft.Extensions.AI.TextContent>(actualChatHistory[1].Contents[1]).Text);

        var fcc = Assert.IsType<Microsoft.Extensions.AI.FunctionCallContent>(actualChatHistory[2].Contents[0]);
        Assert.Equal("call123", fcc.CallId);
        Assert.Equal("FunctionName", fcc.Name);
        Assert.Equal(new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }, fcc.Arguments);

        var frc = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(actualChatHistory[3].Contents[0]);
        Assert.Equal("call123", frc.CallId);
        Assert.Equal("FunctionName", frc.Name);
        Assert.Equal(42, frc.Result);

        Assert.NotNull(actualOptions);
        Assert.Equal("examplemodel", actualOptions.ModelId);
        Assert.Equal(0.2f, actualOptions.Temperature);
        Assert.Equal(128, actualOptions.MaxOutputTokens);
        Assert.Equal(0.5f, actualOptions.FrequencyPenalty);
        Assert.Equal(0.75f, actualOptions.TopP);
        Assert.Equal(["hello"], actualOptions.StopSequences);
        Assert.Equal(42, actualOptions.AdditionalProperties?.TryGetValue("Seed", out int seed) is true ? seed : 0);
        Assert.Equal("user123", actualOptions.AdditionalProperties?["User"]);
    }

    private sealed class TestChatCompletionService : IChatCompletionService
    {
        public IReadOnlyDictionary<string, object?> Attributes { get; set; } = new Dictionary<string, object?>();

        public Func<ChatHistory, PromptExecutionSettings?, Kernel?, CancellationToken, Task<IReadOnlyList<ChatMessageContent>>>? GetChatMessageContentsAsyncDelegate { get; set; }

        public Func<ChatHistory, PromptExecutionSettings?, Kernel?, CancellationToken, IAsyncEnumerable<StreamingChatMessageContent>>? GetStreamingChatMessageContentsAsyncDelegate { get; set; }

        public Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            return this.GetChatMessageContentsAsyncDelegate != null
                ? this.GetChatMessageContentsAsyncDelegate(chatHistory, executionSettings, kernel, cancellationToken)
                : throw new NotImplementedException();
        }

        public IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(ChatHistory chatHistory, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            return this.GetStreamingChatMessageContentsAsyncDelegate != null
                ? this.GetStreamingChatMessageContentsAsyncDelegate(chatHistory, executionSettings, kernel, cancellationToken)
                : throw new NotImplementedException();
        }
    }

    private sealed class TestChatClient : IChatClient
    {
        public ChatClientMetadata Metadata { get; set; } = new();

        public Func<IList<ChatMessage>, ChatOptions?, CancellationToken, Task<Microsoft.Extensions.AI.ChatCompletion>>? CompleteAsyncDelegate { get; set; }

        public Func<IList<ChatMessage>, ChatOptions?, CancellationToken, IAsyncEnumerable<StreamingChatCompletionUpdate>>? CompleteStreamingAsyncDelegate { get; set; }

        public Task<Microsoft.Extensions.AI.ChatCompletion> CompleteAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            return this.CompleteAsyncDelegate != null
                ? this.CompleteAsyncDelegate(chatMessages, options, cancellationToken)
                : throw new NotImplementedException();
        }

        public IAsyncEnumerable<StreamingChatCompletionUpdate> CompleteStreamingAsync(IList<ChatMessage> chatMessages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            return this.CompleteStreamingAsyncDelegate != null
                ? this.CompleteStreamingAsyncDelegate(chatMessages, options, cancellationToken)
                : throw new NotImplementedException();
        }

        public void Dispose() { }

        public TService? GetService<TService>(object? key = null) where TService : class
        {
            return null;
        }
    }

    private sealed class TestEmbeddingGenerationService : IEmbeddingGenerationService<string, float>
    {
        public IReadOnlyDictionary<string, object?> Attributes { get; set; } = new Dictionary<string, object?>();

        public Func<IList<string>, Kernel?, CancellationToken, Task<IList<ReadOnlyMemory<float>>>>? GenerateEmbeddingsAsyncDelegate { get; set; }

        public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            return this.GenerateEmbeddingsAsyncDelegate != null
                ? this.GenerateEmbeddingsAsyncDelegate(data, kernel, cancellationToken)
                : throw new NotImplementedException();
        }
    }

    private sealed class TestEmbeddingGenerator : IEmbeddingGenerator<string, Embedding<float>>
    {
        public EmbeddingGeneratorMetadata Metadata { get; set; } = new();

        public void Dispose() { }

        public Func<IEnumerable<string>, EmbeddingGenerationOptions?, CancellationToken, Task<GeneratedEmbeddings<Embedding<float>>>>? GenerateAsyncDelegate { get; set; }

        public Task<GeneratedEmbeddings<Embedding<float>>> GenerateAsync(IEnumerable<string> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
        {
            return this.GenerateAsyncDelegate != null
                ? this.GenerateAsyncDelegate(values, options, cancellationToken)
                : throw new NotImplementedException();
        }

        public TService? GetService<TService>(object? key = null) where TService : class
        {
            return null;
        }
    }
}
