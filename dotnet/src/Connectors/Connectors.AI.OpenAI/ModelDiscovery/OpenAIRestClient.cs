// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ModelDiscovery;

[System.Diagnostics.CodeAnalysis.SuppressMessage("Build",
    "CA1812:'AzureModelInfo' is an internal class that is apparently never instantiated.", Justification = "JSON object")]
internal sealed class OpenAIRestClient
{
    private const string OpenAiEndpoint = "https://api.openai.com/v1";

    public static async Task<IDictionary<string, OpenAIModelInfo>> GetModelsAsync(
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        CancellationToken cancellationToken = default)
    {
        var modelList = await GetRestDataAsync<ModelList>(
            $"{OpenAiEndpoint}/models",
            apiKey,
            organization,
            httpClient,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return modelList?.Data.ToDictionary(m => m.Id) ?? new(0);
    }

    private static async Task<T?> GetRestDataAsync<T>(
        string endpoint,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(apiKey, nameof(apiKey));

        using HttpClient? localClient = httpClient != null ? null : new HttpClient();
        httpClient ??= localClient;

        using HttpRequestMessage request = new HttpRequestMessage(
            HttpMethod.Get,
            endpoint);
        request.Headers.Add("Authorization", $"Bearer {apiKey}");

        if (!string.IsNullOrWhiteSpace(organization))
        {
            request.Headers.Add("OpenAI-Organization", organization);
        }

        var response = await httpClient!.SendAsync(request, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        var responseStream = await response.Content.ReadAsStreamAsync().ConfigureAwait(false);

        JsonSerializerOptions options = new JsonSerializerOptions();
        options.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.CamelCase));

        return await JsonSerializer.DeserializeAsync<T>(
            responseStream,
            options,
            cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    private sealed class ModelList
    {
        [JsonPropertyName("data")]
        public List<OpenAIModelInfo> Data { get; set; } = new();
    }
}
