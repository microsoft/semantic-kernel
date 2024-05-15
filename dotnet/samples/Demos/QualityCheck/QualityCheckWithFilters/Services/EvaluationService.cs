// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using QualityCheckWithFilters.Models;

namespace QualityCheckWithFilters.Services;

/// <summary>
/// Service which performs HTTP requests to evaluation server.
/// </summary>
internal sealed class EvaluationService(HttpClient httpClient, string endpoint)
{
    public async Task<TResponse> EvaluateAsync<TRequest, TResponse>(TRequest request)
        where TRequest : EvaluationRequest
    {
        var requestContent = new StringContent(JsonSerializer.Serialize(request), Encoding.UTF8, "application/json");

        var response = await httpClient.PostAsync(new Uri(endpoint, UriKind.Relative), requestContent);

        response.EnsureSuccessStatusCode();

        var responseContent = await response.Content.ReadAsStringAsync();

        return JsonSerializer.Deserialize<TResponse>(responseContent) ??
            throw new Exception("Response is not available.");
    }
}
