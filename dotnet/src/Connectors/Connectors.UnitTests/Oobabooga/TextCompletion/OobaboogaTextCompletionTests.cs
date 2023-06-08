// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Oobabooga.TextCompletion;

/// <summary>
/// Unit tests for <see cref="OobaboogaTextCompletion"/> class.
/// </summary>
public sealed class OobaboogaTextCompletionTests : IDisposable
{
    private const string EndPoint = "https://fake-random-test-host";
    private const int BlockingPort = 1234;
    private const int StreamingPort = 2345;
    private const string CompletionText = "fake-test";

    private HttpMessageHandlerStub _messageHandlerStub;
    private HttpClient _httpClient;
    private Uri _endPointUri;
    private string _streamCompletionResponseStub;

    public OobaboogaTextCompletionTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(OobaboogaTestHelper.GetTestResponse("completion_test_response.json"));
        this._streamCompletionResponseStub = OobaboogaTestHelper.GetTestResponse("completion_test_streaming_response.json");

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._endPointUri = new Uri(EndPoint);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        using var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

        //Act
        await sut.GetCompletionsAsync(CompletionText, new CompleteRequestSettings());

        //Assert
        Assert.True(this._messageHandlerStub.RequestHeaders?.Contains("User-Agent"));

        var values = this._messageHandlerStub.RequestHeaders!.GetValues("User-Agent");

        var value = values.SingleOrDefault();
        Assert.Equal(OobaboogaTextCompletion.HttpUserAgent, value);
    }

    [Fact]
    public async Task ProvidedEndpointShouldBeUsedAsync()
    {
        //Arrange
        using var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

        //Act
        await sut.GetCompletionsAsync(CompletionText, new CompleteRequestSettings());

        //Assert
        Assert.StartsWith(EndPoint, this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task BlockingUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        using var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

        //Act
        await sut.GetCompletionsAsync(CompletionText, new CompleteRequestSettings());
        var expectedUri = new UriBuilder(this._endPointUri);
        expectedUri.Path = OobaboogaTextCompletion.BlockingUriPath;
        expectedUri.Port = BlockingPort;

        //Assert
        Assert.Equal(expectedUri.Uri, this._messageHandlerStub.RequestUri);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        using var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

        //Act
        await sut.GetCompletionsAsync(CompletionText, new CompleteRequestSettings());

        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextCompletionRequest>(this._messageHandlerStub.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equal(CompletionText, requestPayload.Prompt);
    }

    [Fact]
    public async Task ShouldHandleServiceResponseAsync()
    {
        //Arrange
        using var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

        //Act
        var result = await sut.GetCompletionsAsync(CompletionText, new CompleteRequestSettings());

        //Assert
        Assert.NotNull(result);

        var completions = result.SingleOrDefault();
        Assert.NotNull(completions);

        var completion = await completions.GetCompletionAsync();
        Assert.Equal("This is test completion response", completion);
    }

    [Fact]
    public async Task ShouldSendPromptToStreamingServiceAsync()
    {
        var expectedResponse = Encoding.UTF8.GetBytes(this._streamCompletionResponseStub);
        using var server = new WebSocketTestServer($"http://localhost:{StreamingPort}/", request => new ArraySegment<byte>(expectedResponse));
        using var sut = new OobaboogaTextCompletion(
            new Uri("http://localhost/"),
            BlockingPort,
            StreamingPort,
            httpClient: this._httpClient);

        var localResponse = sut.CompleteStreamAsync(CompletionText, new CompleteRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 7,
            TopP = 0.1,
        });
        var completion = localResponse.ToEnumerable().Aggregate((s, s1) => s + s1);
        //Assert
        var requestPayload = JsonSerializer.Deserialize<TextCompletionRequest>(server.RequestContent);
        Assert.NotNull(requestPayload);

        Assert.Equal(CompletionText, requestPayload.Prompt);
    }

    [Fact]
    public async Task ShouldHandleStreamingServiceResponseAsync()
    {
        var expectedResponse = Encoding.UTF8.GetBytes(this._streamCompletionResponseStub);

        using var server = new WebSocketTestServer($"http://localhost:{StreamingPort}/", request => new ArraySegment<byte>(expectedResponse));
        using var sut = new OobaboogaTextCompletion(
            new Uri("http://localhost/"),
            BlockingPort,
            StreamingPort,
            httpClient: this._httpClient);

        var localResponse = sut.CompleteStreamAsync(CompletionText, new CompleteRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 7,
            TopP = 0.1,
        });

        var completion = localResponse.ToEnumerable().Aggregate((s, s1) => s + s1);

        Assert.Equal("This is test completion response", completion);
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }
}
