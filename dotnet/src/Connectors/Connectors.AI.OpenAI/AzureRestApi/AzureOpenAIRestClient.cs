// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureRestApi;
internal sealed class AzureOpenAIRestClient
{
    public static async Task<IDictionary<string, AzureDeployment>> GetDeploymentsAsync(
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

    public static async Task<IDictionary<string, AzureModel>> GetModelsAsync(
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

        return modelList?.Data.ToDictionary(m => m.Id) ?? new(0);
    }

    private static async Task<T?> GetRestDataAsync<T>(
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(endpoint, nameof(endpoint));
        Verify.NotNullOrWhiteSpace(apiKey, nameof(apiKey));

        using HttpClient? localClient = (httpClient != null) ? null : new HttpClient();
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

    private class ModelList
    {
        [JsonPropertyName("data")]
        public List<AzureModel> Data { get; set; } = new();
    }

    private class DeploymentList
    {
        [JsonPropertyName("data")]
        public List<AzureDeployment> Data { get; set; } = new();
    }
}

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor.
internal sealed class AzureDeployment
{
    /// <summary>
    /// The OpenAI model to deploy. Can be a base model or a fine tune.
    /// </summary>
    [JsonPropertyName("model")]
    public string Model { get; set; }

    /// <summary>
    /// The owner of this deployment. For Azure OpenAI only "organization-owner" is supported.
    /// </summary>
    [JsonPropertyName("owner")]
    public string Owner { get; set; }

    /// <summary>
    /// The identity of this item.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// The state of a job or item.
    /// </summary>
    [JsonPropertyName("status")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public OperationState Status { get; set; }

    /// <summary>
    /// A timestamp when this job or item was created (in unix epochs).
    /// </summary>
    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    /// <summary>
    /// A timestamp when this job or item was last updated (in unix epochs).
    /// </summary>
    [JsonPropertyName("updated_at")]
    public long UpdatedAt { get; set; }
}

internal sealed class AzureModel
{
    /// <summary>
    /// The identity of this item.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// The base model ID if this is a fine tune model; otherwise null.
    /// </summary>
    [JsonPropertyName("model")]
    public string? FineTuneBaseModel { get; set; }

    /// <summary>
    /// The fine tune job ID if this is a fine tune model; otherwise null.
    /// </summary>
    [JsonPropertyName("fine_tune")]
    public string? FineTune { get; set; }

    /// <summary>
    /// The capabilities of a base or fine tune model.
    /// </summary>
    [JsonPropertyName("capabilities")]
    public ModelCapabilities Capabilities { get; set; }

    /// <summary>
    /// A timestamp when this job or item was created (in unix epochs).
    /// </summary>
    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    /// <summary>
    /// A timestamp when this job or item was modified last (in unix epochs).
    /// </summary>
    [JsonPropertyName("updated_at")]
    public long UpdatedAt { get; set; }
}

internal sealed class ModelCapabilities
{
    /// <summary>
    /// A value indicating whether a model supports completion.
    /// </summary>
    [JsonPropertyName("completion")]
    public bool SupportsTextCompletion { get; set; }

    /// <summary>
    /// A value indicating whether a model supports embeddings.
    /// </summary>
    [JsonPropertyName("embeddings")]
    public bool SupportsEmbeddings { get; set; }
}

internal enum OperationState
{
    Canceled,
    Deleted,
    Failed,
    NotRunning,
    Running,
    Succeeded
}

internal class TimeConverters
{
    private static readonly DateTime s_epochStartUtc = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

    internal static DateTime DateTimeFromUnixEpoch(long secondsAfterUnixEpoch)
        => s_epochStartUtc.AddSeconds(secondsAfterUnixEpoch);
}

#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor.
