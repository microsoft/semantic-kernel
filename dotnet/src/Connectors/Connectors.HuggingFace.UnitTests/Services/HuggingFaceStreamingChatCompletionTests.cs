// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

public sealed class HuggingFaceStreamingChatCompletionTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;

    public HuggingFaceStreamingChatCompletionTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("chatcompletion_test_stream_response.txt"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false)
        {
            BaseAddress = new Uri("https://fake-random-test-host/fake-path")
        };
    }

    [Fact]
    public async Task ShouldContainModelInRequestBodyAsync()
    {
        // Arrange
        string modelId = "fake-model234";
        var client = this.CreateChatCompletionClient(modelId: modelId);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);

        Assert.Contains(modelId, requestContent, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldContainRolesInRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        var request = JsonSerializer.Deserialize<ChatCompletionRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Collection(request.Messages!,
            item => Assert.Equal(chatHistory[0].Role, new AuthorRole(item.Role!)),
            item => Assert.Equal(chatHistory[1].Role, new AuthorRole(item.Role!)),
            item => Assert.Equal(chatHistory[2].Role, new AuthorRole(item.Role!)));
    }

    [Fact]
    public async Task ShouldReturnValidChatResponseAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("Explain me world in many word ;)");

        var testDataResponse = HuggingFaceTestHelper.GetTestResponse("chatcompletion_test_stream_response.txt");
        var responseChunks = Regex.Matches(testDataResponse, @"data:(\{.*\})");

        // Act
        var chatMessageContents = await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert

        Assert.NotEmpty(chatMessageContents);
        Assert.Equal(responseChunks.Count, chatMessageContents.Count);

        var i = -1;
        foreach (Match match in responseChunks)
        {
            i++;
            JsonElement jsonDeltaChunk = JsonElement.Parse(match.Groups[1].Value)
                .GetProperty("choices")[0]
                .GetProperty("delta");

            Assert.Equal(jsonDeltaChunk.GetProperty("content").GetString(), chatMessageContents[i].Content);
            Assert.Equal(jsonDeltaChunk.GetProperty("role").GetString(), chatMessageContents[i].Role.ToString());
        }
    }

    [Fact]
    public async Task ShouldReturnValidMetadataAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var testDataResponse = HuggingFaceTestHelper.GetTestResponse("chatcompletion_test_stream_response.txt");
        var responseChunks = Regex.Matches(testDataResponse, @"data:(\{.*\})");

        // Act
        var chatMessageContents =
            await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        var i = -1;
        foreach (Match match in responseChunks)
        {
            i++;
            var messageChunk = chatMessageContents[i];

            JsonElement jsonRootChunk = JsonElement.Parse(match.Groups[1].Value);

            Assert.NotNull(messageChunk.Metadata);
            Assert.IsType<HuggingFaceChatCompletionMetadata>(messageChunk.Metadata);

            var metadata = messageChunk.Metadata as HuggingFaceChatCompletionMetadata;

            Assert.Equal(jsonRootChunk.GetProperty("id").GetString(), metadata!.Id);
            Assert.Equal(jsonRootChunk.GetProperty("created").GetInt64(), metadata.Created);
            Assert.Equal(jsonRootChunk.GetProperty("object").GetString(), metadata.Object);
            Assert.Equal(jsonRootChunk.GetProperty("model").GetString(), metadata.Model);
            Assert.Equal(jsonRootChunk.GetProperty("system_fingerprint").GetString(), metadata.SystemFingerPrint);
            Assert.Equal(jsonRootChunk.GetProperty("choices")[0].GetProperty("finish_reason").GetString(), metadata.FinishReason);

            var options = new JsonSerializerOptions();
            options.Converters.Add(new DoubleConverter());
            Assert.Equal(jsonRootChunk.GetProperty("choices")[0].GetProperty("logprobs").GetRawText(), JsonSerializer.Serialize(metadata.LogProbs, options));
        }
    }

    [Fact]
    public async Task ShouldUsePromptExecutionSettingsAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var executionSettings = new HuggingFacePromptExecutionSettings()
        {
            MaxTokens = 102,
            Temperature = 0.45f,
            TopP = 0.6f,
            LogProbs = true,
            Seed = 123,
            Stop = ["test"],
            TopLogProbs = 10,
            PresencePenalty = 0.5f,
        };

        // Act
        await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: executionSettings, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        var request = JsonSerializer.Deserialize<ChatCompletionRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Equal(executionSettings.MaxTokens, request.MaxTokens);
        Assert.Equal(executionSettings.Temperature, request.Temperature);
        Assert.Equal(executionSettings.TopP, request.TopP);
        Assert.Equal(executionSettings.LogProbs, request.LogProbs);
        Assert.Equal(executionSettings.Seed, request.Seed);
        Assert.Equal(executionSettings.Stop, request.Stop);
        Assert.Equal(executionSettings.PresencePenalty, request.PresencePenalty);
        Assert.Equal(executionSettings.TopLogProbs, request.TopLogProbs);
    }

    [Fact]
    public async Task ShouldNotPassConvertedSystemMessageToUserMessageToRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        string message = "System message";
        var chatHistory = new ChatHistory(message);
        chatHistory.AddUserMessage("Hello");

        // Act
        await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        var request = JsonSerializer.Deserialize<ChatCompletionRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        var systemMessage = request.Messages![0].Content;
        var messageRole = new AuthorRole(request.Messages[0].Role!);

        Assert.Equal(AuthorRole.System, messageRole);
        Assert.Equal(message, systemMessage);
    }

    [Fact]
    public async Task ItCreatesPostRequestIfBearerIsSpecifiedWithAuthorizationHeaderAsync()
    {
        // Arrange
        string apiKey = "fake-key";
        var client = this.CreateChatCompletionClient(apiKey: apiKey);
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.NotNull(this._messageHandlerStub.RequestHeaders.Authorization);
        Assert.Equal($"Bearer {apiKey}", this._messageHandlerStub.RequestHeaders.Authorization.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.Equal(HttpMethod.Post, this._messageHandlerStub.Method);
    }

    [Fact]
    public async Task ItCreatesPostRequestWithValidUserAgentAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();

        // Act
        await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, this._messageHandlerStub.RequestHeaders.UserAgent.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestWithSemanticKernelVersionHeaderAsync()
    {
        // Arrange
        var client = this.CreateChatCompletionClient();
        var chatHistory = CreateSampleChatHistory();
        var expectedVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(HuggingFaceClient));

        // Act
        await client.StreamCompleteChatMessageAsync(chatHistory, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        var header = this._messageHandlerStub.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    private static ChatHistory CreateSampleChatHistory()
    {
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi");
        chatHistory.AddUserMessage("How are you?");
        return chatHistory;
    }

    private HuggingFaceMessageApiClient CreateChatCompletionClient(
        string modelId = "fake-model",
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null)
    {
        return new HuggingFaceMessageApiClient(
                modelId: modelId,
                apiKey: apiKey,
                endpoint: endpoint,
                httpClient: httpClient ?? this._httpClient);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    private sealed class DoubleConverter : JsonConverter<double>
    {
        public override double Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            return reader.GetSingle();
        }

        public override void Write(Utf8JsonWriter writer, double value, JsonSerializerOptions options)
        {
            var numberString = value.ToString("0.############################", CultureInfo.InvariantCulture);

            // Trim unnecessary trailing zeros and possible trailing decimal point
            numberString = numberString.TrimEnd('0').TrimEnd('.');

            writer.WriteRawValue(numberString);
        }
    }
}
