// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.Oobabooga.TextCompletion;

/// <summary>
/// Unit tests for <see cref="OobaboogaTextCompletion"/> class.
/// </summary>
public sealed class OobaboogaTextCompletionTests : IDisposable
{
    private readonly XunitLogger<OobaboogaTextCompletion> _logger;
    private const string EndPoint = "https://fake-random-test-host";
    private const int BlockingPort = 1234;
    private const int StreamingPort = 2345;
    private const string CompletionText = "fake-test";
    private const string CompletionMultiText = "Hello, my name is";

    private HttpMessageHandlerStub _messageHandlerStub;
    private HttpClient _httpClient;
    private Uri _endPointUri;
    private string _streamCompletionResponseStub;

    public OobaboogaTextCompletionTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<OobaboogaTextCompletion>(output);
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
        var sut = new OobaboogaTextCompletion(endpoint: this._endPointUri,
            blockingPort: BlockingPort,
            httpClient: this._httpClient,
            logger: this._logger);

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
        var sut = new OobaboogaTextCompletion(endpoint: this._endPointUri,
            blockingPort: BlockingPort,
            httpClient: this._httpClient,
            logger: this._logger);

        //Act
        await sut.GetCompletionsAsync(CompletionText, new CompleteRequestSettings());

        //Assert
        Assert.StartsWith(EndPoint, this._messageHandlerStub.RequestUri?.AbsoluteUri, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task BlockingUrlShouldBeBuiltSuccessfullyAsync()
    {
        //Arrange
        var sut = new OobaboogaTextCompletion(endpoint: this._endPointUri,
            blockingPort: BlockingPort,
            httpClient: this._httpClient,
            logger: this._logger);

        //Act
        await sut.GetCompletionsAsync(CompletionText, new CompleteRequestSettings());
        var expectedUri = new UriBuilder(this._endPointUri)
        {
            Path = OobaboogaTextCompletion.BlockingUriPath,
            Port = BlockingPort
        };

        //Assert
        Assert.Equal(expectedUri.Uri, this._messageHandlerStub.RequestUri);
    }

    [Fact]
    public async Task ShouldSendPromptToServiceAsync()
    {
        //Arrange
        var sut = new OobaboogaTextCompletion(endpoint: this._endPointUri,
            blockingPort: BlockingPort,
            httpClient: this._httpClient,
            logger: this._logger);

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
        var sut = new OobaboogaTextCompletion(endpoint: this._endPointUri,
            blockingPort: BlockingPort,
            httpClient: this._httpClient,
            logger: this._logger);

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
        var requestMessage = CompletionText;
        var expectedResponse = new List<string> { this._streamCompletionResponseStub };
        await this.RunWebSocketMultiPacketStreamingTestAsync(
            requestMessage: requestMessage,
            expectedResponse: expectedResponse,
            isPersistent: true).ConfigureAwait(false);
    }

    [Fact]
    public async Task ShouldHandleStreamingServiceTransientWebSocketResponseAsync()
    {
        var requestMessage = CompletionText;
        var expectedResponse = new List<string> { this._streamCompletionResponseStub };
        await this.RunWebSocketMultiPacketStreamingTestAsync(
            requestMessage: requestMessage,
            expectedResponse: expectedResponse).ConfigureAwait(false);
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

        await using var server = new WebSocketTestServer(serverUrl, request =>
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
                await client.CloseAsync(WebSocketCloseStatus.NormalClosure, "Close connection after message received", CancellationToken.None).ConfigureAwait(false);

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
    public async Task ShouldHandleMultiPacketStreamingServiceTransientWebSocketResponseAsync()
    {
        await this.RunWebSocketMultiPacketStreamingTestAsync().ConfigureAwait(false);
    }

    [Fact]
    public async Task ShouldHandleMultiPacketStreamingServicePersistentWebSocketResponseBroadcastBlockAsync()
    {
        await this.RunWebSocketMultiPacketStreamingTestAsync(isPersistent: true).ConfigureAwait(false);
    }

    [Fact]
    public async Task ShouldHandleConcurrentMultiPacketStreamingServiceTransientWebSocketResponseAsync()
    {
        await this.RunWebSocketMultiPacketStreamingTestAsync(nbConcurrentCalls: 10).ConfigureAwait(false);
    }

    [Fact]
    public async Task ShouldHandleConcurrentMultiPacketStreamingServicePersistentWebSocketResponseAsync()
    {
        await this.RunWebSocketMultiPacketStreamingTestAsync(nbConcurrentCalls: 10, isPersistent: true).ConfigureAwait(false);
    }

    /// <summary>
    /// This test will assess concurrent enumeration of the same long multi message (500 websocket messages) streaming result.
    /// </summary>
    [Fact]
    public async Task ShouldHandleConcurrentEnumerationOfLongStreamingServiceResponseAsync()
    {
        var expectedResponse = Enumerable.Range(0, 500).Select(i => i.ToString(CultureInfo.InvariantCulture)).ToList();
        using SemaphoreSlim enforcedConcurrentCallSemaphore = new(20);
        await this.RunWebSocketMultiPacketStreamingTestAsync(
            expectedResponse: expectedResponse,
            nbConcurrentCalls: 1,
            nbConcurrentEnumeration: 100,
            isPersistent: true,
            keepAliveWebSocketsDuration: 100,
            concurrentCallsTicksDelay: 0,
            enforcedConcurrentCallSemaphore: enforcedConcurrentCallSemaphore,
            maxExpectedNbClients: 20).ConfigureAwait(false);
    }

    private async Task RunWebSocketMultiPacketStreamingTestAsync(
        string requestMessage = CompletionMultiText,
        List<string>? expectedResponse = null,
        int nbConcurrentCalls = 1,
        int nbConcurrentEnumeration = 1,
        bool isPersistent = false,
        int requestProcessingDuration = 0,
        int segmentMessageDelay = 0,
        int keepAliveWebSocketsDuration = 100,
        int concurrentCallsTicksDelay = 0,
        SemaphoreSlim? enforcedConcurrentCallSemaphore = null,
        int maxExpectedNbClients = 0,
        int maxTestDuration = 0)
    {
        if (expectedResponse == null)
        {
            expectedResponse = new List<string> { " John", ". I", "'m a", " writer" };
        }

        Func<ClientWebSocket>? webSocketFactory = null;
        // Counter to track the number of WebSocket clients created
        int clientCount = 0;
        var delayTimeSpan = new TimeSpan(concurrentCallsTicksDelay);
        if (isPersistent)
        {
            ClientWebSocket ExternalWebSocketFactory()
            {
                this._logger?.LogInformation(message: "Creating new client web socket");
                var toReturn = new ClientWebSocket();
                return toReturn;
            }

            if (maxExpectedNbClients > 0)
            {
                ClientWebSocket IncrementFactory()
                {
                    var toReturn = ExternalWebSocketFactory();
                    Interlocked.Increment(ref clientCount);
                    return toReturn;
                }

                webSocketFactory = IncrementFactory;
            }
            else
            {
                webSocketFactory = ExternalWebSocketFactory;
            }
        }

        using var cleanupToken = new CancellationTokenSource();

        var sut = new OobaboogaTextCompletion(
            endpoint: new Uri("http://localhost/"),
            streamingPort: StreamingPort,
            httpClient: this._httpClient,
            webSocketsCleanUpCancellationToken: cleanupToken.Token,
            webSocketFactory: webSocketFactory,
            keepAliveWebSocketsDuration: keepAliveWebSocketsDuration,
            concurrentSemaphore: enforcedConcurrentCallSemaphore,
            logger: this._logger);

        await using var server = new OobaboogaWebSocketTestServer($"http://localhost:{StreamingPort}/", request => expectedResponse, logger: this._logger)
        {
            RequestProcessingDelay = TimeSpan.FromMilliseconds(requestProcessingDuration),
            SegmentMessageDelay = TimeSpan.FromMilliseconds(segmentMessageDelay)
        };

        var sw = Stopwatch.StartNew();
        var tasks = new List<Task<IAsyncEnumerable<string>>>();

        for (int i = 0; i < nbConcurrentCalls; i++)
        {
            tasks.Add(Task.Run(() =>
            {
                var localResponse = sut.CompleteStreamAsync(requestMessage, new CompleteRequestSettings()
                {
                    Temperature = 0.01,
                    MaxTokens = 7,
                    TopP = 0.1,
                }, cancellationToken: cleanupToken.Token);
                return localResponse;
            }));
        }

        var callEnumerationTasks = new List<Task<List<string>>>();
        await Task.WhenAll(tasks).ConfigureAwait(false);

        foreach (var callTask in tasks)
        {
            callEnumerationTasks.AddRange(Enumerable.Range(0, nbConcurrentEnumeration).Select(_ => Task.Run(async () =>
            {
                var completion = await callTask.ConfigureAwait(false);
                var result = new List<string>();
                await foreach (var chunk in completion)
                {
                    result.Add(chunk);
                }

                return result;
            })));

            // Introduce a delay between creating each WebSocket client
            await Task.Delay(delayTimeSpan).ConfigureAwait(false);
        }

        var allResults = await Task.WhenAll(callEnumerationTasks).ConfigureAwait(false);

        var elapsed = sw.ElapsedMilliseconds;
        if (maxExpectedNbClients > 0)
        {
            Assert.InRange(clientCount, 1, maxExpectedNbClients);
        }

        // Validate all results
        foreach (var result in allResults)
        {
            Assert.Equal(expectedResponse.Count, result.Count);
            for (int i = 0; i < expectedResponse.Count; i++)
            {
                Assert.Equal(expectedResponse[i], result[i]);
            }
        }

        if (maxTestDuration > 0)
        {
            Assert.InRange(elapsed, 0, maxTestDuration);
        }
    }

    public void Dispose()
    {
        this._httpClient.Dispose();
        this._messageHandlerStub.Dispose();
        this._logger.Dispose();
    }
}
