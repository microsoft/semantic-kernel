// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.HuggingFace.Core;
using Microsoft.SemanticKernel.Http;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

public sealed class HuggingFaceStreamingTextGenerationTests : IDisposable
{
    private readonly HttpClient _httpClient;
    private readonly HttpMessageHandlerStub _messageHandlerStub;
    private const string SamplePrompt = "Hello, How are you?";

    public HuggingFaceStreamingTextGenerationTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(HuggingFaceTestHelper.GetTestResponse("textgeneration_test_stream_response.txt"));

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
    }

    [Fact]
    public async Task SpecifiedServiceModelShouldBeUsedAsync()
    {
        //Arrange
        string modelId = "fake-model234";
        var client = this.CreateTextGenerationClient(modelId: modelId);

        //Act
        await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: null, cancellationToken: CancellationToken.None).ToListAsync();

        //Assert
        Assert.EndsWith($"/{modelId}", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task SpecifiedExecutionSettingseModelShouldBeUsedAsync()
    {
        //Arrange
        string modelId = "fake-model234";
        var client = this.CreateTextGenerationClient();

        //Act
        await client.StreamGenerateTextAsync(SamplePrompt, executionSettings: new PromptExecutionSettings { ModelId = modelId }, cancellationToken: CancellationToken.None).ToListAsync();

        //Assert
        Assert.EndsWith($"/{modelId}", this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ShouldReturnValidChatResponseAsync()
    {
        // Arrange
        var client = this.CreateTextGenerationClient();
        var testDataResponse = HuggingFaceTestHelper.GetTestResponse("textgeneration_test_stream_response.txt");
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
            JsonElement jsonTokenChunk = JsonElement.Parse(match.Groups[1].Value)
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
        var testDataResponse = HuggingFaceTestHelper.GetTestResponse("textgeneration_test_stream_response.txt");
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

            JsonElement jsonRootChunk = JsonElement.Parse(match.Groups[1].Value);

            Assert.NotNull(messageChunk.Metadata);
            Assert.IsType<HuggingFaceTextGenerationStreamMetadata>(messageChunk.Metadata);

            var metadata = messageChunk.Metadata as HuggingFaceTextGenerationStreamMetadata;

            Assert.Equal(jsonRootChunk.GetProperty("index").GetInt32(), metadata!.Index);
            Assert.Equal(jsonRootChunk.GetProperty("generated_text").GetString(), metadata.GeneratedText);
            Assert.Equal(jsonRootChunk.GetProperty("token").GetProperty("id").GetInt32(), metadata.TokenId);
            Assert.Equal(jsonRootChunk.GetProperty("token").GetProperty("logprob").GetDouble(), metadata!.TokenLogProb);
            Assert.Equal(jsonRootChunk.GetProperty("token").GetProperty("special").GetBoolean(), metadata!.TokenSpecial);

            if (jsonRootChunk.GetProperty("details").ValueKind == JsonValueKind.Object)
            {
                Assert.Equal(jsonRootChunk.GetProperty("details").GetProperty("finish_reason").GetString(), metadata.FinishReason);
                Assert.Equal(jsonRootChunk.GetProperty("details").GetProperty("generated_tokens").GetInt32(), metadata.GeneratedTokens);
            }
        }
    }

    [Fact]
    public async Task ShouldUsePromptExecutionSettingsAsync()
    {
        // Arrange
        var client = this.CreateTextGenerationClient();
        var executionSettings = new HuggingFacePromptExecutionSettings()
        {
            MaxTokens = null,
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
        Assert.Equal(executionSettings.Details, request.Parameters.Details);
        Assert.Equal(executionSettings.MaxTime, request.Parameters.MaxTime);
        Assert.Equal(executionSettings.WaitForModel, request.Options!.WaitForModel);
        Assert.Equal(executionSettings.UseCache, request.Options.UseCache);
    }

    [Fact]
    public async Task ShouldHaveModelIdDefinedWhenProvidedInServiceAsync()
    {
        // Arrange
        var expectedModel = "service-model";
        var client = this.CreateTextGenerationClient(expectedModel);

        // Act
        await foreach (var textContent in client.StreamGenerateTextAsync(SamplePrompt, executionSettings: null, cancellationToken: CancellationToken.None))
        {
            // Assert
            Assert.NotNull(textContent!.ModelId);
            Assert.Equal(expectedModel, textContent.ModelId);
        }
    }

    [Fact]
    public async Task ShouldHaveModelIdDefinedWhenProvidedInExecutionSettingsAsync()
    {
        // Arrange
        var client = this.CreateTextGenerationClient();
        var expectedModel = "execution-settings-model";

        // Act
        await foreach (var textContent in client.StreamGenerateTextAsync(SamplePrompt, executionSettings: new PromptExecutionSettings { ModelId = expectedModel }, cancellationToken: CancellationToken.None))
        {
            // Assert
            Assert.NotNull(textContent!.ModelId);
            Assert.Equal(expectedModel, textContent.ModelId);
        }
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
