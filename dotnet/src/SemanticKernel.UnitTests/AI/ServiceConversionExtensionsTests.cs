// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using Moq;
using SemanticKernel.UnitTests.Utilities;
using Xunit;

namespace SemanticKernel.UnitTests.AI;

public class ServiceConversionExtensionsTests
{
    [Fact]
    [Obsolete("Temporary test for Obsolete ITextEmbeddingGenerationService")]
    public void EmbeddingGenerationInvalidArgumentsThrow()
    {
        Assert.Throws<ArgumentNullException>("service", () => EmbeddingGenerationExtensions.AsEmbeddingGenerator<string, float>(null!));
        Assert.Throws<ArgumentNullException>("generator", () => EmbeddingGenerationExtensions.AsEmbeddingGenerationService<string, float>(null!));
    }

    [Fact]
    public void ChatCompletionInvalidArgumentsThrow()
    {
        Assert.Throws<ArgumentNullException>("service", () => ChatCompletionServiceExtensions.AsChatClient(null!));
        Assert.Throws<ArgumentNullException>("client", () => Microsoft.SemanticKernel.ChatCompletion.ChatClientExtensions.AsChatCompletionService(null!));
    }

    [Fact]
    [Obsolete("Temporary test for Obsolete ITextEmbeddingGenerationService")]
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
        var metadata = Assert.IsType<EmbeddingGeneratorMetadata>(generator.GetService(typeof(EmbeddingGeneratorMetadata)));
        Assert.Equal(nameof(TestEmbeddingGenerationService), metadata.ProviderName);
        Assert.Equal("examplemodel", metadata.DefaultModelId);
        Assert.Equal("https://example.com/", metadata.ProviderUri?.ToString());
    }

    [Fact]
    [Obsolete("Temporary test for Obsolete ITextEmbeddingGenerationService")]
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
        var metadata = Assert.IsType<ChatClientMetadata>(client.GetService(typeof(ChatClientMetadata)));
        Assert.Equal(nameof(TestChatCompletionService), metadata.ProviderName);
        Assert.Equal("examplemodel", metadata.DefaultModelId);
        Assert.Equal("https://example.com/", metadata.ProviderUri?.ToString());
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
    [Obsolete("Temporary test for Obsolete ITextEmbeddingGenerationService")]
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

        ReadOnlyMemory<float> embedding = await generator.GenerateVectorAsync("some text");
        Assert.Equal([1f, 2f, 3f], embedding.ToArray());
    }

    [Fact]
    [Obsolete("Temporary test for Obsolete ITextEmbeddingGenerationService")]
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

        Microsoft.Extensions.AI.ChatResponse result = await client.GetResponseAsync([
            new(ChatRole.System,
            [
                new Microsoft.Extensions.AI.TextContent("some text"),
                new Microsoft.Extensions.AI.UriContent("http://imageurl", mediaType: "image/jpeg"),
            ]),
            new(ChatRole.User,
            [
                new Microsoft.Extensions.AI.UriContent("http://audiourl", mediaType: "audio/mpeg"),
                new Microsoft.Extensions.AI.TextContent("some other text"),
            ]),
            new(ChatRole.Assistant,
            [
                new Microsoft.Extensions.AI.FunctionCallContent("call123", "FunctionName", new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }),
            ]),
            new(ChatRole.Tool,
            [
                new Microsoft.Extensions.AI.FunctionResultContent("call123", 42),
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
        Assert.Equal("the result", result.Text);

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
        Assert.Null(frc.FunctionName);
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

        await client.GetResponseAsync(messages);
        oaiSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(JsonSerializer.Serialize(actualSettings));
        Assert.Null(oaiSettings);

        await client.GetResponseAsync(messages, new() { ResponseFormat = ChatResponseFormat.Text });
        oaiSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(JsonSerializer.Serialize(actualSettings));
        Assert.Equal("text", oaiSettings?.ResponseFormat?.ToString());

        await client.GetResponseAsync(messages, new() { ResponseFormat = ChatResponseFormat.Json });
        oaiSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(JsonSerializer.Serialize(actualSettings));
        Assert.Equal("json_object", oaiSettings?.ResponseFormat?.ToString());

        await client.GetResponseAsync(messages, new() { ResponseFormat = ChatResponseFormat.ForJsonSchema(JsonElement.Parse("""
            {"type": "string"}
            """)) });
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

        await client.GetResponseAsync(messages, new()
        {
            Tools =
            [
                new NopAIFunction("AIFunc1"),
                new NopAIFunction("AIFunc2"),
                KernelFunctionFactory.CreateFromMethod(() => "invoked", "NiftyFunction"),
                .. KernelPluginFactory.CreateFromFunctions("NiftyPlugin",
                [
                    KernelFunctionFactory.CreateFromMethod(() => "invoked", "NiftyFunction")
                ]),
            ],
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
                Assert.Equal(4, config.Functions?.Count);
                Assert.Equal("AIFunc1", config.Functions?[0].Name);
                Assert.Equal("AIFunc2", config.Functions?[1].Name);
                Assert.Equal("NiftyFunction", config.Functions?[2].Name);
                Assert.Equal("NiftyPlugin_NiftyFunction", config.Functions?[3].Name);
                break;

            case RequiredChatToolMode r:
                Assert.Equal(FunctionChoice.Required, config.Choice);
                if (r.RequiredFunctionName is null)
                {
                    Assert.Equal(4, config.Functions?.Count);
                    Assert.Equal("AIFunc1", config.Functions?[0].Name);
                    Assert.Equal("AIFunc2", config.Functions?[1].Name);
                    Assert.Equal("NiftyFunction", config.Functions?[2].Name);
                    Assert.Equal("NiftyPlugin_NiftyFunction", config.Functions?[3].Name);
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
            await f.InvokeAsync(new());
        }
    }

    private sealed class NopAIFunction(string name) : AIFunction
    {
        public override string Name => name;
        protected override ValueTask<object?> InvokeCoreAsync(AIFunctionArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            return ValueTask.FromResult<object?>(null);
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

        List<ChatResponseUpdate> result = await client.GetStreamingResponseAsync([
            new(ChatRole.System,
            [
                new Microsoft.Extensions.AI.TextContent("some text"),
                new Microsoft.Extensions.AI.UriContent("http://imageurl", "image/jpeg"),
            ]),
            new(ChatRole.User,
            [
                new Microsoft.Extensions.AI.UriContent("http://audiourl", "audio/mpeg"),
                new Microsoft.Extensions.AI.TextContent("some other text"),
            ]),
            new(ChatRole.Assistant,
            [
                new Microsoft.Extensions.AI.FunctionCallContent("call123", "FunctionName", new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }),
            ]),
            new(ChatRole.Tool,
            [
                new Microsoft.Extensions.AI.FunctionResultContent("call123", 42),
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
        Assert.Null(frc.FunctionName);
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
        List<ChatMessage>? actualChatHistory = null;
        ChatOptions? actualOptions = null;

        using IChatClient client = new TestChatClient()
        {
            CompleteAsyncDelegate = async (messages, options, cancellationToken) =>
            {
                await Task.Yield();
                actualChatHistory = messages.ToList();
                actualOptions = options;
                return new Microsoft.Extensions.AI.ChatResponse(new ChatMessage(ChatRole.User, "the result"));
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
        Assert.Equal("http://imageurl/", Assert.IsType<Microsoft.Extensions.AI.UriContent>(actualChatHistory[0].Contents[1]).Uri?.ToString());
        Assert.Equal("http://audiourl/", Assert.IsType<Microsoft.Extensions.AI.UriContent>(actualChatHistory[1].Contents[0]).Uri?.ToString());
        Assert.Equal("some other text", Assert.IsType<Microsoft.Extensions.AI.TextContent>(actualChatHistory[1].Contents[1]).Text);

        var fcc = Assert.IsType<Microsoft.Extensions.AI.FunctionCallContent>(actualChatHistory[2].Contents[0]);
        Assert.Equal("call123", fcc.CallId);
        Assert.Equal("FunctionName", fcc.Name);
        Assert.Equal(new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }, fcc.Arguments);

        var frc = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(actualChatHistory[3].Contents[0]);
        Assert.Equal("call123", frc.CallId);
        Assert.Equal(42, frc.Result);

        Assert.NotNull(actualOptions);
        Assert.Equal("examplemodel", actualOptions.ModelId);
        Assert.Equal(0.2f, actualOptions.Temperature);
        Assert.Equal(128, actualOptions.MaxOutputTokens);
        Assert.Equal(0.5f, actualOptions.FrequencyPenalty);
        Assert.Equal(0.75f, actualOptions.TopP);
        Assert.Equal(["hello"], actualOptions.StopSequences);
        Assert.Equal(42, actualOptions.Seed);
        Assert.Equal("user123", actualOptions.AdditionalProperties?["User"]);
    }

    [Fact]
    public async Task AsChatCompletionServiceStreamingContentConvertedAsExpected()
    {
        List<ChatMessage>? actualChatHistory = null;
        ChatOptions? actualOptions = null;

        using IChatClient client = new TestChatClient()
        {
            CompleteStreamingAsyncDelegate = (messages, options, cancellationToken) =>
            {
                actualChatHistory = messages.ToList();
                actualOptions = options;
                return new List<ChatResponseUpdate>()
                {
                    new(ChatRole.Assistant, "the result")
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
        Assert.Equal("http://imageurl/", Assert.IsType<Microsoft.Extensions.AI.UriContent>(actualChatHistory[0].Contents[1]).Uri?.ToString());
        Assert.Equal("http://audiourl/", Assert.IsType<Microsoft.Extensions.AI.UriContent>(actualChatHistory[1].Contents[0]).Uri?.ToString());
        Assert.Equal("some other text", Assert.IsType<Microsoft.Extensions.AI.TextContent>(actualChatHistory[1].Contents[1]).Text);

        var fcc = Assert.IsType<Microsoft.Extensions.AI.FunctionCallContent>(actualChatHistory[2].Contents[0]);
        Assert.Equal("call123", fcc.CallId);
        Assert.Equal("FunctionName", fcc.Name);
        Assert.Equal(new Dictionary<string, object?>() { ["key1"] = "value1", ["key2"] = "value2" }, fcc.Arguments);

        var frc = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(actualChatHistory[3].Contents[0]);
        Assert.Equal("call123", frc.CallId);
        Assert.Equal(42, frc.Result);

        Assert.NotNull(actualOptions);
        Assert.Equal("examplemodel", actualOptions.ModelId);
        Assert.Equal(0.2f, actualOptions.Temperature);
        Assert.Equal(128, actualOptions.MaxOutputTokens);
        Assert.Equal(0.5f, actualOptions.FrequencyPenalty);
        Assert.Equal(0.75f, actualOptions.TopP);
        Assert.Equal(["hello"], actualOptions.StopSequences);
        Assert.Equal(42, actualOptions.Seed);
        Assert.Equal("user123", actualOptions.AdditionalProperties?["User"]);
    }

    [Theory]
    [InlineData(true, false)]
    [InlineData(true, true)]
    [InlineData(false, false)]
    [InlineData(false, true)]
    public async Task ChatClientFunctionResultPreservesMetadataAsync(bool includeMetadata, bool returnNull)
    {
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => returnNull ? null : "result", "TestFunction");
        kernel.Plugins.AddFromFunctions("test", [function]);
        kernel.AutoFunctionInvocationFilters.Add(new MetadataFilter(includeMetadata));

        var (toolMessage, history) = await InvokeFunctionThroughChatClientAsync(kernel);

        Assert.Null(toolMessage.AdditionalProperties);
        var aiResult = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(Assert.Single(toolMessage.Contents));
        Assert.Equal("call1", aiResult.CallId);
        Assert.Equal(returnNull ? "Success: Function completed." : "result", aiResult.Result);
        Assert.Equal(includeMetadata ? "value" : null, aiResult.AdditionalProperties?["key"]);

        var historyMessage = Assert.Single(history, message => message.Role == AuthorRole.Tool);
        Assert.False(historyMessage.Metadata?.ContainsKey("key") ?? false);
        var result = Assert.Single(historyMessage.Items.OfType<Microsoft.SemanticKernel.FunctionResultContent>());
        Assert.Equal(aiResult.Result, result.Result);
        Assert.Equal(includeMetadata ? "value" : null, result.Metadata?["key"]);
    }

    [Fact]
    public async Task ChatClientFunctionResultMetadataDoesNotChangeFunctionOutputAsync()
    {
        var kernel = new Kernel();
        kernel.Plugins.AddFromFunctions("test", [KernelFunctionFactory.CreateFromMethod(() => "result", "TestFunction")]);
        kernel.AutoFunctionInvocationFilters.Add(new MetadataFilter(true, new Dictionary<string, object?> { ["key"] = "metadata-marker" }));

        // The function invoking client writes the function output to its trace log, which is the same text it records in telemetry.
        var logger = new FakeLogger();
        var loggerFactory = new Mock<ILoggerFactory>();
        loggerFactory.Setup(factory => factory.CreateLogger(It.IsAny<string>())).Returns(logger);

        var (toolMessage, _) = await InvokeFunctionThroughChatClientAsync(kernel, loggerFactory.Object);

        Assert.Contains(logger.Logs, log => log.Message.Contains("\"result\"", StringComparison.Ordinal));
        Assert.DoesNotContain(logger.Logs, log => log.Message.Contains("metadata-marker", StringComparison.Ordinal));
        var result = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(Assert.Single(toolMessage.Contents));
        Assert.Equal("result", result.Result);
        Assert.Equal("metadata-marker", result.AdditionalProperties?["key"]);
    }

    [Fact]
    public async Task ChatClientFunctionResultAcceptsMetadataKeysDifferingOnlyByCaseAsync()
    {
        var kernel = new Kernel();
        kernel.Plugins.AddFromFunctions("test", [KernelFunctionFactory.CreateFromMethod(() => "result", "TestFunction")]);
        kernel.AutoFunctionInvocationFilters.Add(new MetadataFilter(true, new Dictionary<string, object?> { ["Id"] = 1, ["id"] = 2 }));

        var (toolMessage, _) = await InvokeFunctionThroughChatClientAsync(kernel);

        var result = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(Assert.Single(toolMessage.Contents));
        Assert.Equal("result", result.Result);
        Assert.Null(result.Exception);
        Assert.Equal("id", Assert.Single(result.AdditionalProperties!).Key, ignoreCase: true);
    }

    [Fact]
    public async Task ChatClientFunctionResultMetadataStaysWithItsCallWhenCallIdsRepeatAsync()
    {
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(
            (KernelFunction function, string input) => new FunctionResult(function, input, metadata: new Dictionary<string, object?> { ["key"] = input }),
            "TestFunction");
        kernel.Plugins.AddFromFunctions("test", [function]);

        // Some providers do not supply call IDs, so both calls carry the same empty ID.
        var (toolMessage, _) = await InvokeFunctionThroughChatClientAsync(kernel, createFunctionCalls: tool =>
        [
            new Microsoft.Extensions.AI.FunctionCallContent(string.Empty, tool.Name, new Dictionary<string, object?> { ["input"] = "first" }),
            new Microsoft.Extensions.AI.FunctionCallContent(string.Empty, tool.Name, new Dictionary<string, object?> { ["input"] = "second" }),
        ]);

        var results = toolMessage.Contents.OfType<Microsoft.Extensions.AI.FunctionResultContent>().ToArray();
        Assert.Equal(2, results.Length);
        Assert.Equal("first", results[0].Result?.ToString());
        Assert.Equal("first", results[0].AdditionalProperties?["key"]);
        Assert.Equal("second", results[1].Result?.ToString());
        Assert.Equal("second", results[1].AdditionalProperties?["key"]);
    }

    [Fact]
    public async Task ChatClientFunctionResultPreservesExistingResultContentAsync()
    {
        var kernel = new Kernel();
        var existingResult = new Microsoft.Extensions.AI.FunctionResultContent("call1", "result")
        {
            AdditionalProperties = new() { ["existing"] = "original", ["key"] = "old" }
        };
        var function = KernelFunctionFactory.CreateFromMethod(() => existingResult, "TestFunction");
        kernel.Plugins.AddFromFunctions("test", [function]);
        kernel.AutoFunctionInvocationFilters.Add(new MetadataFilter(true));

        var (toolMessage, _) = await InvokeFunctionThroughChatClientAsync(kernel);

        var result = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(Assert.Single(toolMessage.Contents));
        Assert.NotSame(existingResult, result);
        Assert.Equal("result", result.Result);
        Assert.Equal("original", result.AdditionalProperties?["existing"]);
        Assert.Equal("value", result.AdditionalProperties?["key"]);
        Assert.Equal("old", existingResult.AdditionalProperties?["key"]);
    }

    [Fact]
    public async Task StreamingChatClientFunctionResultPreservesMetadataAsync()
    {
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "result", "TestFunction");
        kernel.Plugins.AddFromFunctions("test", [function]);
        kernel.AutoFunctionInvocationFilters.Add(new MetadataFilter(true));

        ChatMessage? toolMessage = null;
        int requests = 0;
        async IAsyncEnumerable<ChatResponseUpdate> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options, [EnumeratorCancellation] CancellationToken _)
        {
            await Task.Yield();
            if (requests++ == 0)
            {
                var tool = Assert.Single(options!.Tools!.OfType<AIFunction>());
                yield return new ChatResponseUpdate(ChatRole.Assistant, [new Microsoft.Extensions.AI.FunctionCallContent("call1", tool.Name)]);
            }
            else
            {
                toolMessage = Assert.Single(messages, message => message.Role == ChatRole.Tool);
                yield return new ChatResponseUpdate(ChatRole.Assistant, "done");
            }
        }

        using var innerClient = new TestChatClient { CompleteStreamingAsyncDelegate = GetResponseAsync };
        using var client = new ChatClientBuilder(innerClient).UseKernelFunctionInvocation().Build();
        var service = client.AsChatCompletionService();
        ChatHistory history = [new ChatMessageContent(AuthorRole.User, "hello")];

        await foreach (var _ in service.GetStreamingChatMessageContentsAsync(history, new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }, kernel))
        {
        }

        Assert.NotNull(toolMessage);
        Assert.Null(toolMessage.AdditionalProperties);
        var aiResult = Assert.IsType<Microsoft.Extensions.AI.FunctionResultContent>(Assert.Single(toolMessage.Contents));
        Assert.Equal("result", aiResult.Result);
        Assert.Equal("value", aiResult.AdditionalProperties?["key"]);
        var historyMessage = Assert.Single(history, message => message.Role == AuthorRole.Tool);
        Assert.False(historyMessage.Metadata?.ContainsKey("key") ?? false);
        var result = Assert.Single(historyMessage.Items.OfType<Microsoft.SemanticKernel.FunctionResultContent>());
        Assert.Equal("result", result.Result);
        Assert.Equal("value", result.Metadata?["key"]);
    }

    /// <summary>
    /// Runs one chat request in which the model calls the only function of the kernel.
    /// Returns the tool message sent back to the model and the resulting chat history.
    /// </summary>
    private static async Task<(ChatMessage ToolMessage, ChatHistory History)> InvokeFunctionThroughChatClientAsync(
        Kernel kernel,
        ILoggerFactory? loggerFactory = null,
        Func<AIFunction, IList<AIContent>>? createFunctionCalls = null)
    {
        ChatMessage? toolMessage = null;
        int requests = 0;
        using var innerClient = new TestChatClient
        {
            CompleteAsyncDelegate = (messages, options, _) =>
            {
                if (requests++ == 0)
                {
                    var tool = Assert.Single(options!.Tools!.OfType<AIFunction>());
                    var functionCalls = createFunctionCalls?.Invoke(tool) ?? [new Microsoft.Extensions.AI.FunctionCallContent("call1", tool.Name)];
                    return Task.FromResult(new Microsoft.Extensions.AI.ChatResponse(new ChatMessage(ChatRole.Assistant, functionCalls)));
                }

                toolMessage = Assert.Single(messages, message => message.Role == ChatRole.Tool);
                return Task.FromResult(new Microsoft.Extensions.AI.ChatResponse(new ChatMessage(ChatRole.Assistant, "done")));
            }
        };
        using var client = new ChatClientBuilder(innerClient).UseKernelFunctionInvocation(loggerFactory).Build();
        var service = client.AsChatCompletionService();
        ChatHistory history = [new ChatMessageContent(AuthorRole.User, "hello")];

        await service.GetChatMessageContentsAsync(history, new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }, kernel);

        Assert.NotNull(toolMessage);
        return (toolMessage, history);
    }

    private sealed class MetadataFilter(bool includeMetadata, IReadOnlyDictionary<string, object?>? metadata = null) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            await next(context);
            if (includeMetadata)
            {
                context.Result = new FunctionResult(context.Function, context.Result.GetValue<object>(), context.Result.Culture,
                    metadata ?? new Dictionary<string, object?> { ["key"] = "value" });
            }
        }
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

        public Func<IEnumerable<ChatMessage>, ChatOptions?, CancellationToken, Task<Microsoft.Extensions.AI.ChatResponse>>? CompleteAsyncDelegate { get; set; }

        public Func<IEnumerable<ChatMessage>, ChatOptions?, CancellationToken, IAsyncEnumerable<ChatResponseUpdate>>? CompleteStreamingAsyncDelegate { get; set; }

        public Task<Microsoft.Extensions.AI.ChatResponse> GetResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            return this.CompleteAsyncDelegate != null
                ? this.CompleteAsyncDelegate(messages, options, cancellationToken)
                : throw new NotImplementedException();
        }

        public IAsyncEnumerable<ChatResponseUpdate> GetStreamingResponseAsync(IEnumerable<ChatMessage> messages, ChatOptions? options = null, CancellationToken cancellationToken = default)
        {
            return this.CompleteStreamingAsyncDelegate != null
                ? this.CompleteStreamingAsyncDelegate(messages, options, cancellationToken)
                : throw new NotImplementedException();
        }

        public void Dispose() { }

        public object? GetService(Type serviceType, object? serviceKey = null)
        {
            return serviceType == typeof(ChatClientMetadata) ? this.Metadata : null;
        }
    }

    [Obsolete("Temporary test for Obsolete ITextEmbeddingGenerationService")]
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

        public object? GetService(Type serviceType, object? serviceKey = null)
        {
            return serviceType.IsInstanceOfType(this.Metadata) ? this.Metadata : null;
        }
    }
}
