// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;

namespace SemanticKernel.Service.Services;

public record AnalysisResult(
    [property: JsonPropertyName("category")] string Category,
    [property: JsonPropertyName("riskLevel")] short RiskLevel
);

public record ImageContent([property: JsonPropertyName("content")] string Content);

public record ImageAnalysisRequest(
    [property: JsonPropertyName("image")] ImageContent Image,
    [property: JsonPropertyName("categories")] List<string> Categories
);

public sealed class AzureContentModerator : IDisposable
{
    private const string HttpUserAgent = "Copilot Chat";

    private readonly Uri _endpoint;
    private readonly HttpClient _httpClient;
    private readonly HttpClientHandler? _httpClientHandler;

    private static readonly List<string> s_categories = new()
    {
        "Hate",
        "Sexual",
        "SelfHarm",
        "Violence" };

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureContentModerator"/> class.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="apiKey">The API key.</param>
    /// <param name="httpClientHandler">Instance of <see cref="HttpClientHandler"/> to setup specific scenarios.</param>
    public AzureContentModerator(Uri endpoint, string apiKey, HttpClientHandler httpClientHandler)
    {
        this._endpoint = endpoint;
        this._httpClient = new(httpClientHandler);

        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);

        // HACK
        this._httpClient.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", apiKey);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureContentModerator"/> class.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="apiKey">The API key.</param>
    public AzureContentModerator(Uri endpoint, string apiKey)
    {
        this._endpoint = endpoint;

        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this._httpClient = new(this._httpClientHandler);

        this._httpClient.DefaultRequestHeaders.Add("User-Agent", HttpUserAgent);

        // HACK
        this._httpClient.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", apiKey);
    }

    /// <summary>
    /// Prase the analysis result and return the violated categories.
    /// </summary>
    /// <param name="analysisResult">The content analysis result.</param>
    /// <param name="threshold">The violation threshold.</param>
    /// <returns>The list of violated category names. Will return an empty list if there is no violoation.</returns>
    public static List<string> ParseViolatedCategories(Dictionary<string, AnalysisResult> analysisResult, short threshold)
    {
        var violatedCategories = new List<string>();

        foreach (var category in analysisResult.Values)
        {
            if (category.RiskLevel > threshold)
            {
                violatedCategories.Add(category.Category);
            }
        }
        return violatedCategories;
    }
    public async Task<Dictionary<string, AnalysisResult>> ImageAnalysisAsync(string base64Image, CancellationToken cancellationToken)
    {
        var image = base64Image.Replace("data:image/png;base64,", "", StringComparison.InvariantCultureIgnoreCase).Replace("data:image/jpeg;base64,", "", StringComparison.InvariantCultureIgnoreCase);
        ImageContent content = new(image);
        ImageAnalysisRequest requestBody = new(content, s_categories);
        using var httpRequestMessage = new HttpRequestMessage()
        {
            Method = HttpMethod.Post,
            RequestUri = new Uri($"{this._endpoint}/contentmoderator/image:analyze?api-version=2022-12-30-preview"),
            Content = new StringContent(JsonSerializer.Serialize(requestBody), Encoding.UTF8, "application/json"),
        };
        var response = await this._httpClient.SendAsync(httpRequestMessage, cancellationToken).ConfigureAwait(false);
        var body = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode || body is null)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Content moderator: Failed analyzing the image. {response.StatusCode}");
        }
        var result = JsonSerializer.Deserialize<Dictionary<string, AnalysisResult>>(body!);
        if (result is null)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                "Content moderator: Failed analyzing the image");
        }
        return result;
    }
    /// <inheritdoc/>
    public void Dispose()
    {
        this._httpClient.Dispose();
        this._httpClientHandler?.Dispose();
    }
}
