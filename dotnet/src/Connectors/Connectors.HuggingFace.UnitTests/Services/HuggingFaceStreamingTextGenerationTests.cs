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
using Microsoft.SemanticKernel.Connectors.HuggingFace.Client;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Client.Models;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Text;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

public sealed class HuggingFaceStreamingTextGenerationTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string SamplePrompt = "Hello, How are you?";

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

    public HuggingFaceStreamingTextGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("textgeneration_test_stream_response.txt"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task ShouldContainModelInRequestBodyAsync()
    {
        // Arrange
        string modelId = "fake-model234";
        var client = this.CreateTextGenerationClient(modelId: modelId);

        // Act
        await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestContent);
        var requestContent = Encoding.UTF8.GetString(this._messageHandlerStub.RequestContent);

        Assert.Contains(modelId, requestContent, StringComparison.Ordinal);
    }

    [Fact]
    public async Task ShouldReturnValidChatResponseAsync()
    {
        // Arrange
        var client = this.CreateTextGenerationClient();
        var testDataResponse = HuggingFaceTestHelper.GetTestResponse("chatcompletion_test_stream_response.txt");
        var responseChunks = Regex.Matches(testDataResponse, @"data:(\{.*\})");

        // Act
        var textChunks = await client.StreamGenerateTextAsync("Hello, Explain me world in many word ;)", executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert

        Assert.NotEmpty(textChunks);
        Assert.Equal(responseChunks.Count, textChunks.Count);

        var i = -1;
        foreach (Match match in responseChunks)
        {
            i++;
            JsonElement jsonTokenChunk = JsonSerializer.Deserialize<JsonElement>(match.Groups[1].Value)
                .GetProperty("token");

            Assert.Equal(jsonTokenChunk
                .GetProperty("text")
                .GetString(), textChunks[i].Text);
        }
    }

    [Fact]
    public async Task ShouldReturnValidMetadataAsync()
    {
        // Arrange
        var client = this.CreateTextGenerationClient();
        var testDataResponse = HuggingFaceTestHelper.GetTestResponse("chatcompletion_test_stream_response.txt");
        var responseChunks = Regex.Matches(testDataResponse, @"data:(\{.*\})");

        // Act
        var chatMessageContents =
            await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        var i = -1;
        foreach (Match match in responseChunks)
        {
            i++;
            var messageChunk = chatMessageContents[i];

            JsonElement jsonRootChunk = JsonSerializer.Deserialize<JsonElement>(match.Groups[1].Value);

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
        var client = this.CreateTextGenerationClient();
        var executionSettings = new HuggingFacePromptExecutionSettings()
        {
            MaxTokens = 102,
            Temperature = 0.45f,
            TopP = 0.6f,
            TopK = 10,
            RepetitionPenalty = 0.8f,
            ResultsPerPrompt = 5,
            MaxTime = 1000,
            WaitForModel = true,
            UseCache = true,
        };

        // Act
        await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: executionSettings, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        var request = JsonSerializer.Deserialize<TextGenerationRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(request);
        Assert.Equal(executionSettings.MaxTokens, request.Parameters!.MaxNewTokens);
        Assert.Equal(executionSettings.Temperature, request.Parameters.Temperature);
        Assert.Equal(executionSettings.TopP, request.Parameters.TopP);
        Assert.Equal(executionSettings.TopK, request.Parameters.TopK);
        Assert.Equal(executionSettings.RepetitionPenalty, request.Parameters.RepetitionPenalty);
        Assert.Equal(executionSettings.ResultsPerPrompt, request.Parameters.NumReturnSequences);
        Assert.Equal(executionSettings.MaxTime, request.Parameters.MaxTime);
        Assert.Equal(executionSettings.WaitForModel, request.Options!.WaitForModel);
        Assert.Equal(executionSettings.UseCache, request.Options.UseCache);
    }

    [Fact]
    public async Task ItCreatesPostRequestIfBearerIsSpecifiedWithAuthorizationHeaderAsync()
    {
        // Arrange
        string apiKey = "fake-key";
        var client = this.CreateTextGenerationClient(apiKey: apiKey);

        // Act
        await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.NotNull(this._messageHandlerStub.RequestHeaders.Authorization);
        Assert.Equal($"Bearer {apiKey}", this._messageHandlerStub.RequestHeaders.Authorization.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestAsync()
    {
        // Arrange
        var client = this.CreateTextGenerationClient();

        // Act
        await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.Equal(HttpMethod.Post, this._messageHandlerStub.Method);
    }

    [Fact]
    public async Task ItCreatesPostRequestWithValidUserAgentAsync()
    {
        // Arrange
        var client = this.CreateTextGenerationClient();

        // Act
        await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, this._messageHandlerStub.RequestHeaders.UserAgent.ToString());
    }

    [Fact]
    public async Task ItCreatesPostRequestWithSemanticKernelVersionHeaderAsync()
    {
        // Arrange
        var client = this.CreateTextGenerationClient();
        var expectedVersion = HttpHeaderConstant.Values.GetAssemblyVersion(typeof(HuggingFaceClient));

        // Act
        await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        // Assert
        Assert.NotNull(this._messageHandlerStub.RequestHeaders);
        var header = this._messageHandlerStub.RequestHeaders.GetValues(HttpHeaderConstant.Names.SemanticKernelVersion).SingleOrDefault();
        Assert.NotNull(header);
        Assert.Equal(expectedVersion, header);
    }

    private HuggingFaceClient CreateTextGenerationClient(
        string modelId = "fake-model",
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null)
        => new(
            modelId: modelId,
            apiKey: apiKey,
            endpoint: endpoint,
            httpClient: httpClient ?? this._httpClient);

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
