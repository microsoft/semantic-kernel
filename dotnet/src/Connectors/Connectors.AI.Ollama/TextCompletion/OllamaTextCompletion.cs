using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Http;

using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;


namespace Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;


/// <summary>
/// Allows semantic kernel to use models hosted using Ollama as AI Service
/// </summary>
public class OllamaTextCompletion : ITextCompletion
{
    public IReadOnlyDictionary<string, string> Attributes => this._attributes;

    private readonly Dictionary<string, string> _attributes = new();
    private readonly HttpClient _httpClient;
    private readonly ILogger<OllamaTextCompletion> _logger;


    /// <summary>
    /// 
    /// </summary>
    /// <param name="model_id">Ollama model to use</param>
    /// <param name="base_url">Ollama endpoint</param>
    /// <param name="loggerFactory">Logger</param>
    public OllamaTextCompletion(string model_id, string base_url, ILoggerFactory? loggerFactory)
    {
        this._attributes.Add("model_id", model_id);
        this._attributes.Add("base_url", base_url);

        this._httpClient = new HttpClient(NonDisposableHttpClientHandler.Instance, disposeHandler: false);

        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger<OllamaTextCompletion>() : NullLogger<OllamaTextCompletion>.Instance;

        this.PingOllamaAsync().Wait();
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
    private async Task PingOllamaAsync()
    {
        var data = new
        {
            name = this.Attributes["model_id"]
        };

        using var request = HttpRequest.CreatePostRequest($"{this.Attributes["base_url"]}/api/generate", data);

        request.Headers.Add("User-Agent", HttpHeaderValues.UserAgent);

        using var response = await this._httpClient.SendWithSuccessCheckAsync(request, CancellationToken.None).ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        this._logger.LogInformation($"Connected to Ollama at {this.Attributes["base_url"]} with model {this.Attributes["model_id"]}");
    }
}
