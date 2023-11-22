// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;

/// <summary>
/// Allows semantic kernel to use models hosted using Ollama as AI Service
/// </summary>
#pragma warning disable CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
public class OllamaTextCompletion : ITextCompletion
#pragma warning restore CA1001 // Types that own disposable fields should be disposable. No need to dispose the Http client here. It can either be an internal client using NonDisposableHttpClientHandler or an external client managed by the calling code, which should handle its disposal.
{
    public IReadOnlyDictionary<string, string> Attributes => this._attributes;

    private readonly Dictionary<string, string> _attributes = new();
    private readonly HttpClient _httpClient;
    private readonly ILogger<OllamaTextCompletion> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextCompletion"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="model_id">Ollama model to use</param>
    /// <param name="base_url">Ollama endpoint</param>
    /// <param name="loggerFactory">Logger</param>
    public OllamaTextCompletion(string model_id, string base_url, ILoggerFactory? loggerFactory)
    {
        Verify.NotNull(base_url);
        Verify.NotNullOrWhiteSpace(model_id);

        this._attributes.Add("model_id", model_id);
        this._attributes.Add("base_url", base_url);

        this._httpClient = new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);

        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger<OllamaTextCompletion>() : NullLogger<OllamaTextCompletion>.Instance;
    }

    /// <summary>
    /// Generate response using Ollama api
    /// </summary>
    /// <param name="text">Prompt</param>
    /// <param name="requestSettings">Llama2 Settings can be passed as extension data</param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        var data = new
        {
            model = this.Attributes["model_id"],
            prompt = text,
            stream = false,
            options = requestSettings?.ExtensionData,
        };

        using var request = HttpRequest.CreatePostRequest($"{this.Attributes["base_url"]}/api/generate", data);

        request.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);

        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        var json = JsonSerializer.Deserialize<JsonNode>(await response.Content.ReadAsStringAsync().ConfigureAwait(false));

        return new List<ITextResult> { new OllamaTextResponse(new Orchestration.ModelResult(json!["response"]!.GetValue<string>())) };
    }

    /// <summary>
    /// !NOTE : Haven't tested, Not sure if this works
    /// </summary>
    /// <param name="text">Prompt</param>
    /// <param name="requestSettings">Llama2 Settings can be passed as extension data</param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, AIRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        var data = new
        {
            model = this.Attributes["model_id"],
            prompt = text,
            stream = true,
            options = requestSettings?.ExtensionData,
        };

        using var request = HttpRequest.CreatePostRequest($"{this.Attributes["base_url"]}/api/generate", data);

        request.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);

        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, cancellationToken).ConfigureAwait(false);

        var stream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);

        using (stream)
        {
            using var reader = new StreamReader(stream);

            var done = false;

            while (!done)
            {
                var json = JsonSerializer.Deserialize<JsonNode>(
                    await response.Content.ReadAsStringAsync().ConfigureAwait(false)
                );

                done = json!["done"]!.GetValue<bool>();

                yield return new OllamaTextStreamingResponse(new Orchestration.ModelResult(json!["response"]!.GetValue<string>()));
            }
        }
    }

    /// <summary>
    /// Pings ollama to see if the required model is running.
    /// </summary>
    /// <returns></returns>
    public async Task PingOllamaAsync()
    {
        var data = new
        {
            name = this.Attributes["model_id"]
        };

        using var request = HttpRequest.CreatePostRequest($"{this.Attributes["base_url"]}/api/show", data);

        request.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);

        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, CancellationToken.None).ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        this._logger.LogInformation($"Connected to Ollama at {this.Attributes["base_url"]} with model {this.Attributes["model_id"]}");
    }
}
