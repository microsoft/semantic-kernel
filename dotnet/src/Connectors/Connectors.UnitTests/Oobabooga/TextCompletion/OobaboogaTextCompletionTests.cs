// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Oobabooga.TextCompletion;

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously. System.Linq.Async Nuget package should be used globally eventually

/// <summary>
/// Unit tests for <see cref="OobaboogaTextCompletion"/> class.
/// </summary>
public sealed class OobaboogaTextCompletionTests : IDisposable
{
    private const string EndPoint = "https://fake-random-test-host";
    private const int BlockingPort = 1234;
    private const int StreamingPort = 2345;
    private const string CompletionText = "fake-test";
    private const string CompletionMultiText = "Hello, my name is";

    private HttpMessageHandlerStub _messageHandlerStub;
    private HttpClient _httpClient;
    private Func<ClientWebSocket> _webSocketFactory;
    private List<ClientWebSocket> _webSockets = new List<ClientWebSocket>();
    private Uri _endPointUri;
    private string _streamCompletionResponseStub;

    public OobaboogaTextCompletionTests()
    {
        this._messageHandlerStub = new HttpMessageHandlerStub();
        this._messageHandlerStub.ResponseToReturn.Content = new StringContent(OobaboogaTestHelper.GetTestResponse("completion_test_response.json"));
        this._streamCompletionResponseStub = OobaboogaTestHelper.GetTestResponse("completion_test_streaming_response.json");

        this._httpClient = new HttpClient(this._messageHandlerStub, false);
        this._webSocketFactory = () =>
        {
            var toReturn = new ClientWebSocket();
            this._webSockets.Add(toReturn);
            return toReturn;
        };
        this._endPointUri = new Uri(EndPoint);
    }

    [Fact]
    public async Task UserAgentHeaderShouldBeUsedAsync()
    {
        //Arrange
        var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

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
        var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

        //Act
        await sut.GetCompletionsAsync(CompletionText, new CompleteRequestSettings());

        //Assert
        Assert.StartsWith(EndPoint, this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task BlockingUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

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
        var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

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
        var sut = new OobaboogaTextCompletion(this._endPointUri, BlockingPort, StreamingPort, httpClient: this._httpClient);

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
    public async Task ShouldHandleStreamingServicePersistentWebSocketResponseAsync()
    {
        var sut = new OobaboogaTextCompletion(
            new Uri("http://localhost/"),
            BlockingPort,
            StreamingPort,
            httpClient: this._httpClient,
            webSocketFactory: this._webSocketFactory);

        this.ShouldHandleStreamingServiceResponseAsync(sut);
    }

    [Fact]
    public async Task ShouldHandleStreamingServiceTransientWebSocketResponseAsync()
    {
        var sut = new OobaboogaTextCompletion(
            new Uri("http://localhost/"),
            BlockingPort,
            StreamingPort,
            httpClient: this._httpClient);

        this.ShouldHandleStreamingServiceResponseAsync(sut);
    }

    [Fact]
    public async Task ShouldHandleConcurrentWebSocketConnectionsAsync()
    {
        var serverUrl = $"http://localhost:{StreamingPort}/";
        var clientUrl = $"ws://localhost:{StreamingPort}/";
        var expectedResponses = new List<string>
        {
            "Response 1",
            "Response 2",
            "Response 3",
            "Response 4",
            "Response 5"
        };

        using var server = new WebSocketTestServer(serverUrl, request =>
        {
            // Simulate different responses for each request
            var responseIndex = int.Parse(Encoding.UTF8.GetString(request.ToArray()), CultureInfo.InvariantCulture);
            byte[] bytes = Encoding.UTF8.GetBytes(expectedResponses[responseIndex]);
            var toReturn = new List<ArraySegment<byte>> { new ArraySegment<byte>(bytes) };
            return toReturn;
        });

        var tasks = new List<Task<string>>();

        // Simulate multiple concurrent WebSocket connections
        for (int i = 0; i < expectedResponses.Count; i++)
        {
            var currentIndex = i;
            tasks.Add(Task.Run(async () =>
            {
                using var client = new ClientWebSocket();
                await client.ConnectAsync(new Uri(clientUrl), CancellationToken.None);

                // Send a request to the server
                var requestBytes = Encoding.UTF8.GetBytes(currentIndex.ToString(CultureInfo.InvariantCulture));
                await client.SendAsync(new ArraySegment<byte>(requestBytes), WebSocketMessageType.Text, true, CancellationToken.None);

                // Receive the response from the server
                var responseBytes = new byte[1024];
                var responseResult = await client.ReceiveAsync(new ArraySegment<byte>(responseBytes), CancellationToken.None);
                await client.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "Close connection after message received", CancellationToken.None).ConfigureAwait(false);

                var response = Encoding.UTF8.GetString(responseBytes, 0, responseResult.Count);

                return response;
            }));
        }

        // Assert
        for (int i = 0; i < expectedResponses.Count; i++)
        {
            var response = await tasks[i].ConfigureAwait(false);
            Assert.Equal(expectedResponses[i], response);
        }
    }

    [Fact]
    public async Task ShouldHandleMultiPacketStreamingServicePersistentWebSocketResponseAsync()
    {
        await this.RunWebSocketMultiPacketStreamingTestAsync(isConcurrent: false, isPersistent: true);
    }

    [Fact]
    public async Task ShouldHandleMultiPacketStreamingServiceTransientWebSocketResponseAsync()
    {
        await this.RunWebSocketMultiPacketStreamingTestAsync(isConcurrent: false, isPersistent: false);
    }

    [Fact]
    public async Task ShouldHandleConcurrentMultiPacketStreamingServicePersistentWebSocketResponseAsync()
    {
        await this.RunWebSocketMultiPacketStreamingTestAsync(isConcurrent: true, isPersistent: true);
    }

    [Fact]
    public async Task ShouldHandleConcurrentMultiPacketStreamingServiceTransientWebSocketResponseAsync()
    {
        await this.RunWebSocketMultiPacketStreamingTestAsync(isConcurrent: true, isPersistent: false);
    }

    private void ShouldHandleStreamingServiceResponseAsync(OobaboogaTextCompletion sut)
    {
        var requestMessage = CompletionText;
        var expectedResponse = this._streamCompletionResponseStub;
        using var server = new OobaboogaWebSocketTestServer($"http://localhost:{StreamingPort}/", request => new List<string>(new[]
        {
            expectedResponse
        }));

        var localResponse = sut.CompleteStreamAsync(requestMessage, new CompleteRequestSettings()
        {
            Temperature = 0.01,
            MaxTokens = 7,
            TopP = 0.1,
        });

        //TODO: use AggregateAsync when System.Linq.Async Nuget package is installed
        var completion = localResponse.ToEnumerable().Aggregate((s, s1) => s + s1);

        // Get the first request content
        var firstRequestContent = server.RequestContents.First().Value;

        var requestPayload = JsonSerializer.Deserialize<TextCompletionRequest>(firstRequestContent);
        Assert.NotNull(requestPayload);
        Assert.Equal(CompletionText, requestPayload.Prompt);
        Assert.Equal(expectedResponse, completion);
    }

    private async Task RunWebSocketMultiPacketStreamingTestAsync(bool isConcurrent, bool isPersistent)
    {
        var requestMessage = CompletionMultiText;
        var expectedResponse = new List<string> { " John", ". I", "'m a", " writer" };
        var webSocketFactory = isPersistent ? this._webSocketFactory : null;
        var sut = new OobaboogaTextCompletion(
            new Uri("http://localhost/"),
            BlockingPort,
            StreamingPort,
            httpClient: this._httpClient,
            webSocketFactory: webSocketFactory);

        using var server = new OobaboogaWebSocketTestServer($"http://localhost:{StreamingPort}/", request => expectedResponse);

        var tasks = new List<Task<List<string>>>();

        for (int i = 0; i < (isConcurrent ? 10 : 1); i++)
        {
            tasks.Add(Task.Run(async () =>
            {
                var localResponse = await sut.CompleteStreamAsync(requestMessage, new CompleteRequestSettings()
                {
                    Temperature = 0.01,
                    MaxTokens = 7,
                    TopP = 0.1,
                }).ToListAsync();
                return localResponse;
            }));
        }

        await Task.WhenAll(tasks);

        foreach (var task in tasks)
        {
            var completion = await task;

            // Assert
            Assert.Equal(expectedResponse.Count, completion.Count);
            for (int i = 0; i < expectedResponse.Count; i++)
            {
                Assert.Equal(expectedResponse[i], completion[i]);
            }
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
        foreach (ClientWebSocket clientWebSocket in this._webSockets)
        {
            clientWebSocket.Dispose();
        }
    }
}
