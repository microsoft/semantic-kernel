// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.WebSockets;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

/// <summary>
/// Oobabooga text completion service API.
/// Adapted from https://github.com/oobabooga/text-generation-webui/tree/main/api-examples
/// </summary>
public sealed class OobaboogaTextCompletion : ITextCompletion, IDisposable
{
    private const string HttpUserAgent = "Microsoft-Semantic-Kernel";
    private const string BlockingUriPath = "/api/v1/generate";
    private const string StreamingUriPath = "/api/v1/stream";

    private readonly Uri _endpoint;
    private readonly int _blockingPort;
    private readonly int _streamingPort;
    private readonly HttpClient _httpClient;
    private readonly ClientWebSocket _webSocket;
    private readonly HttpClientHandler? _httpClientHandler;

    /// <summary>
    /// Initializes a new instance of the <see cref="OobaboogaTextCompletion"/> class.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="blockingPort">The port for blocking requests.</param>
    /// <param name="streamingPort">The port for streaming requests.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    public OobaboogaTextCompletion(Uri endpoint, int blockingPort, int streamingPort, HttpClientHandler httpClientHandler)
    {
        Verify.NotNull(endpoint);

        this._endpoint = endpoint;
        this._blockingPort = blockingPort;
        this._streamingPort = streamingPort;

        this._httpClient = new(httpClientHandler);
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);
        this._webSocket = new ClientWebSocket();
        this._webSocket.Options.SetRequestHeader("User-Agent", HttpUserAgent);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OobaboogaTextCompletion"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="blockingPort">The port for blocking requests.</param>
    /// <param name="streamingPort">The port for streaming requests.</param>
    public OobaboogaTextCompletion(Uri endpoint, int blockingPort, int streamingPort)
    {
        Verify.NotNull(endpoint);

        this._endpoint = endpoint;
        this._blockingPort = blockingPort;
        this._streamingPort = streamingPort;

        this._httpClientHandler = new() { CheckCertificateRevocationList = true };

        this._httpClient = new(this._httpClientHandler);
        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);
        this._webSocket = new ClientWebSocket();
        this._webSocket.Options.SetRequestHeader("User-Agent", HttpUserAgent);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ITextCompletionStreamingResult> GetStreamingCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        UriBuilder streamingUri = new(this._endpoint)
        {
            Port = this._streamingPort,
            Path = StreamingUriPath
        };
        if (streamingUri.Uri.Scheme.StartsWith("http", StringComparison.OrdinalIgnoreCase))
        {
            streamingUri.Scheme = (streamingUri.Scheme == "https") ? "wss" : "ws";
        }

        var completionRequest = this.CreateOobaboogaRequest(text, requestSettings);

        var requestBytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(completionRequest));

        using var client = new ClientWebSocket();
        await client.ConnectAsync(streamingUri.Uri, cancellationToken).ConfigureAwait(false);

        var sendSegment = new ArraySegment<byte>(requestBytes);
        await client.SendAsync(sendSegment, WebSocketMessageType.Text, true, cancellationToken).ConfigureAwait(false);

        var buffer = new byte[1024];
        while (client.State == WebSocketState.Open)
        {
            var received = await client.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken).ConfigureAwait(false);

            if (received.MessageType == WebSocketMessageType.Text)
            {
                var body = Encoding.UTF8.GetString(buffer, 0, received.Count);
                var responseObject = JsonSerializer.Deserialize<TextCompletionStreamingResponse>(body);

                if (responseObject is null)
                {
                    throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Unexpected response from model")
                    {
                        Data = { { "ModelResponse", body } },
                    };
                }

                switch (responseObject.Event)
                {
                    case "text_stream":
                        yield return new TextCompletionStreamingResult(responseObject.Text);
                        break;
                    case "stream_end":
                        await client.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None).ConfigureAwait(false);
                        break;
                    default:
                        break;
                }
            }
            else if (received.MessageType == WebSocketMessageType.Close)
            {
                await client.CloseOutputAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None).ConfigureAwait(false);
            }
        }
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextCompletionResult>> GetCompletionsAsync(
        string text,
        CompleteRequestSettings requestSettings,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var blockingUri = new UriBuilder(this._endpoint)
            {
                Port = this._blockingPort,
                Path = BlockingUriPath
            };

            var completionRequest = this.CreateOobaboogaRequest(text, requestSettings);

            using var stringContent = new StringContent(
                JsonSerializer.Serialize(completionRequest),
                Encoding.UTF8,
                "application/json");

            using var httpRequestMessage = new HttpRequestMessage()
            {
                Method = HttpMethod.Post,
                RequestUri = blockingUri.Uri,
                Content = stringContent
            };

            using var response = await this._httpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

            TextCompletionResponse? completionResponse = JsonSerializer.Deserialize<TextCompletionResponse>(body);

            if (completionResponse is null)
            {
                throw new AIException(AIException.ErrorCodes.InvalidResponseContent, "Unexpected response from model")
                {
                    Data = { { "ModelResponse", body } },
                };
            }

            return completionResponse.Results.Select(completionText => new TextCompletionResult(completionText.Text ?? string.Empty)).ToList();
        }
        catch (Exception e) when (e is not AIException && !e.IsCriticalException())
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._httpClient.Dispose();
        this._webSocket.Dispose();
        this._httpClientHandler?.Dispose();
    }

    #region private ================================================================================

    /// <summary>
    /// Creates an Oobabooga request.
    /// </summary>
    /// <param name="text">The text to complete.</param>
    /// <param name="requestSettings">The request settings.</param>
    /// <returns>An OobaboogaTextCompletionRequest.</returns>
    private TextCompletionRequest CreateOobaboogaRequest(string text, CompleteRequestSettings requestSettings)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new ArgumentNullException(nameof(text));
        }

        // Prepare the request using the provided parameters.
        return new TextCompletionRequest()
        {
            Prompt = text,
            MaxNewTokens = requestSettings.MaxTokens,
            Temperature = requestSettings.Temperature,
            TopP = requestSettings.TopP,
            RepetitionPenalty = 0.5f + requestSettings.PresencePenalty,
            StoppingStrings = requestSettings.StopSequences.ToList()
        };
    }

    #endregion
}
