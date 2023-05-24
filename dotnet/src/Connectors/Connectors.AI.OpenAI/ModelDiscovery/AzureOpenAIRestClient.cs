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

internal static class AzureOpenAIRestClient
{
    public static async Task<IDictionary<string, AzureDeploymentInfo>> GetDeploymentsAsync(
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        CancellationToken cancellationToken = default)
    {
        var deploymentList = await GetRestDataAsync<DeploymentList>(
            $"{endpoint}/openai/deployments?api-version=2022-06-01-preview",
            apiKey,
            httpClient,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        return deploymentList?.Data.ToDictionary(d => d.Id) ?? new(0);
    }

    public static async Task<IDictionary<string, AzureModelInfo>> GetModelsAsync(
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        CancellationToken cancellationToken = default)
    {
        var modelList = await GetRestDataAsync<ModelList>(
            $"{endpoint}/openai/models?api-version=2022-06-01-preview",
            apiKey,
            httpClient,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        Dictionary<string, AzureModelInfo> modelDictionary = new(modelList?.Data.Count ?? 0);
        foreach (AzureModelInfo model in modelList?.Data ?? Enumerable.Empty<AzureModelInfo>())
        {
            // Note: .ToDictionary() doesn't work here because the model.Id is not unique.
            modelDictionary[model.Id] = model;
        }

        return modelDictionary;
    }

    private static async Task<T?> GetRestDataAsync<T>(
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(endpoint, nameof(endpoint));
        Verify.NotNullOrWhiteSpace(apiKey, nameof(apiKey));

        using HttpClient? localClient = httpClient != null ? null : new HttpClient();
        httpClient ??= localClient;

        using HttpRequestMessage request = new HttpRequestMessage(
            HttpMethod.Get,
            endpoint);
        request.Headers.Add("api-key", apiKey);

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

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Build",
        "CA1812:'AzureModelInfo' is an internal class that is apparently never instantiated.", Justification = "JSON object")]
    private sealed class ModelList
    {
        [JsonPropertyName("data")]
        public List<AzureModelInfo> Data { get; set; } = new();
    }

    [System.Diagnostics.CodeAnalysis.SuppressMessage("Build",
        "CA1812:'AzureModelInfo' is an internal class that is apparently never instantiated.", Justification = "JSON object")]
    private sealed class DeploymentList
    {
        [JsonPropertyName("data")]
        public List<AzureDeploymentInfo> Data { get; set; } = new();
    }
}
