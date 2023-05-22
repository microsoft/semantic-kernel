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

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.OpenAIRestApi;
internal class OpenAIRestClient
{
    const string OpenAiEndpoint = "https://api.openai.com/v1";

    public static async Task<IDictionary<string, OpenAIModel>> GetModelsAsync(
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

        using HttpClient? localClient = (httpClient != null) ? null : new HttpClient();
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

    private class ModelList
    {
        [JsonPropertyName("data")]
        public List<OpenAIModel> Data { get; set; } = new();
    }
}

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor.
internal sealed class OpenAIModel
{
    private static string[] ChatCompletionModels = { "gpt-4", "gpt-4-0314", "gpt-4-32k", "gpt-4-32k-0314", "gpt-3.5-turbo", "gpt-3.5-turbo-0301" };
    private static string[] TextCompetionModels = { "text-davinci-003", "text-davinci-002", "text-curie-001", "text-babbage-001", "text-ada-001" };
    private static string[] TextEmbeddingModels = { "text-embedding-ada-002", "text-search-ada-doc-001" };

    /// <summary>
    /// The identity of this item.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// The capabilities of a base or fine tune model.
    /// </summary>
    [JsonIgnore]
    public ModelCapabilities Capabilities { get; }

    internal sealed class ModelCapabilities
    {
        public static ModelCapabilities InitializeWithKnownModels(string model)
        {
            return new ModelCapabilities()
            {
                SupportsChatCompletion = ChatCompletionModels.Contains(model, StringComparer.OrdinalIgnoreCase),
                SupportsTextCompletion = TextCompetionModels.Contains(model, StringComparer.OrdinalIgnoreCase),
                SupportsEmbeddings = TextEmbeddingModels.Contains(model, StringComparer.OrdinalIgnoreCase),
            };
        }

        /// <summary>
        /// A value indicating whether a model supports completion.
        /// </summary>
        [JsonPropertyName("chat")]
        public bool SupportsChatCompletion { get; set; }

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
}
#pragma warning restore CS8618
