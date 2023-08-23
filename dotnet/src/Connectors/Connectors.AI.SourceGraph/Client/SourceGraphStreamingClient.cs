// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Models;


internal class SourceGraphStreamingClient : ISourceGraphStreamClient
{
    private readonly SourceGraphClientOptions _config;
    private readonly ILogger _logger;
    private readonly HttpClient _httpClient;


    public SourceGraphStreamingClient(SourceGraphClientOptions config, HttpClient? httpClient = null, ILogger? logger = null)
    {
        _config = config;
        _logger = logger ?? NullLogger.Instance;
        _httpClient = httpClient ?? new HttpClient(NonDisposableHttpClientHandler.Instance, false);
    }


    /// <inheritdoc />
    public async Task<CompletionResponse?> CompleteAsync(
        CompletionsRequest completionsRequest,
        Action<CompletionResponse>? onPartialResponse = null,
        CancellationToken cancellationToken = default)
    {
        var baseUrl = _config.ServerEndpoint;
        using var request = completionsRequest.Build();
        Console.WriteLine(_config.AccessToken);
        var response = await ExecuteHttpRequestAsync(baseUrl, request, cancellationToken).ConfigureAwait(false);

        if (response.Content == null)
        {
            throw new Exception("No response body");
        }

        foreach (var header in response.Content.Headers)
        {
            Console.WriteLine($"{header.Key}: {string.Join(", ", header.Value)}");
        }
        var isStreamingResponse = response.Content?.Headers.ContentType.MediaType == "text/event-stream";
        // get the event stream

        if (isStreamingResponse)
        {
            try
            {
                var stream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);
                var reader = new StreamReader(stream); // do not dispose reader immediately

                CompletionResponse? lastResponse = null;

                while (await reader.ReadLineAsync().ConfigureAwait(false) is { } line)
                {
                    if (line.StartsWith("event: completion", StringComparison.Ordinal) && line.Length > "data: ".Length)
                    {
                        var jsonResponse = line.Substring("data: ".Length);
                        lastResponse = JsonSerializer.Deserialize<CompletionResponse>(jsonResponse);

                        if (lastResponse != null)
                        {
                            onPartialResponse?.Invoke(lastResponse);

                            if (lastResponse.StopReason == "stop_sequence")
                            {
                                break;
                            }
                        }
                    }
                }

                response.Dispose(); // dispose response and reader manually
                reader.Dispose();

                if (lastResponse == null)
                {
                    throw new Exception("No completion response received");
                }

                return lastResponse;
            }
            catch (Exception ex)
            {
                var message = $"Error parsing streaming CodeCompletionResponse: {ex}";
                _logger?.LogError(message);
                throw new Exception(message);
            }
        }
        var responseContent = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

        try
        {
            var completionResponse = JsonSerializer.Deserialize<CompletionResponse>(responseContent);
            return completionResponse;
        }
        catch (Exception ex)
        {
            var message = $"Error parsing CodeCompletionResponse: {ex}";
            _logger?.LogError(message);
            throw new Exception(message);
        }
    }


    private async Task<HttpResponseMessage> ExecuteHttpRequestAsync(
        string baseURL,
        HttpRequestMessage request,
        CancellationToken cancellationToken = default
    )
    {
        request.Headers.Add("Authorization", $"token {_config.AccessToken}");

        if (_config.CustomHeaders != null)
        {
            foreach (KeyValuePair<string, string> header in _config.CustomHeaders)
            {
                request.Headers.Add(header.Key, header.Value);
            }
        }

        request.RequestUri = new Uri(baseURL + request.RequestUri);

        var response = await _httpClient.SendAsync(request, cancellationToken)
            .ConfigureAwait(false);

        if (response.IsSuccessStatusCode)
        {
            _logger.LogDebug("Response succeeded");
            Console.WriteLine("Response succeeded");
        }
        else
        {
            _logger.LogWarning("Response failed");
            Console.WriteLine("Response failed");
        }

        return response;
    }
}
