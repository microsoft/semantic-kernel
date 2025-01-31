// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.AI.CrewAI.Models;

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI.Client;

/// <summary>
/// A client for interacting with the CrewAI Enterprise API.
/// </summary>
internal class CrewAIEntepriseClient : ICrewAIEntepriseClient
{
    private readonly Uri _endpoint;
    private readonly Func<Task<string>> _authTokenProvider;
    private readonly IHttpClientFactory? _httpClientFactory;

    public CrewAIEntepriseClient(Uri endpoint, Func<Task<string>>? authTokenProvider, IHttpClientFactory? clientFactory = null)
    {
        Verify.NotNull(endpoint, nameof(endpoint));
        Verify.NotNull(authTokenProvider, nameof(authTokenProvider));

        this._endpoint = endpoint;
        this._authTokenProvider = authTokenProvider;
        this._httpClientFactory = clientFactory;
    }

    /// <summary>
    /// Get the inputs required for the Crew to kickoff.
    /// </summary>
    /// <returns>Aninstance of <see cref="CrewAIRequiredInputs"/> describing the required inputs.</returns>
    /// <exception cref="KernelException"></exception>
    public async Task<CrewAIRequiredInputs> GetInputsAsync()
    {
        try
        {
            using var client = await this.CreateHttpClientAsync().ConfigureAwait(false);
            var response = await client.GetAsync(new Uri("/inputs", UriKind.Relative)).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();
            var responseString = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            var requirements = JsonSerializer.Deserialize<CrewAIRequiredInputs>(responseString);

            return requirements switch
            {
                null => throw new KernelException(message: "Failed to deserialize requirements from CrewAI."),
                _ => requirements,
            };
        }
        catch (Exception ex)
        {
            throw new KernelException(message: "Failed to get required inputs for CrewAI Crew.", innerException: ex);
        }
    }

    /// <summary>
    /// Kickoff the Crew.
    /// </summary>
    /// <param name="inputs">An object containing key value pairs matching the required inputs of the Crew.</param>
    /// <param name="taskWebhookUrl">The task level webhook Uri.</param>
    /// <param name="stepWebhookUrl">The step level webhook Uri.</param>
    /// <param name="crewWebhookUrl">The crew level webhook Uri.</param>
    /// <returns>A string containing the Id of the started Crew Task.</returns>
    public async Task<CrewAIKickoffResponse> KickoffAsync(
        object? inputs,
        string? taskWebhookUrl = null,
        string? stepWebhookUrl = null,
        string? crewWebhookUrl = null)
    {
        try
        {
            var content = new
            {
                inputs,
                taskWebhookUrl,
                stepWebhookUrl,
                crewWebhookUrl
            };

            using var client = await this.CreateHttpClientAsync().ConfigureAwait(false);
            using var requestContent = new StringContent(JsonSerializer.Serialize(content), Encoding.UTF8, "application/json");
            var response = await client.PostAsync(new Uri("/kickoff", UriKind.Relative), requestContent).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            var strResponse = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            var kickoffResponse = JsonSerializer.Deserialize<CrewAIKickoffResponse>(strResponse);
            return kickoffResponse switch
            {
                null => throw new KernelException(message: "Failed to deserialize kickoff response from CrewAI."),
                _ => kickoffResponse,
            };
        }
        catch (Exception ex)
        {
            throw new KernelException(message: "Failed to kickoff CrewAI Crew.", innerException: ex);
        }
    }

    /// <summary>
    /// Get the status of the Crew Task.
    /// </summary>
    /// <param name="taskId">The Id of the task.</param>
    /// <returns>A string containing the status or final result of the Crew task.</returns>
    /// <exception cref="KernelException"></exception>
    public async Task<CrewAIStatusResponse> GetStatusAsync(string taskId)
    {
        try
        {
            using var client = await this.CreateHttpClientAsync().ConfigureAwait(false);
            var response = await client.GetAsync(new Uri($"/status/{taskId}", UriKind.Relative)).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();
            var strResponse = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            var statusResponse = JsonSerializer.Deserialize<CrewAIStatusResponse>(strResponse);
            return statusResponse switch
            {
                null => throw new KernelException(message: "Failed to deserialize status response from CrewAI."),
                _ => statusResponse,
            };
        }
        catch (Exception ex)
        {
            throw new KernelException(message: "Failed to status of CrewAI Crew.", innerException: ex);
        }
    }

    public void Dispose()
    {
        throw new NotImplementedException();
    }

    #region Private Methods

    private async Task<HttpClient> CreateHttpClientAsync()
    {
        var authToken = await this._authTokenProvider().ConfigureAwait(false);

        if (string.IsNullOrWhiteSpace(authToken))
        {
            throw new KernelException(message: "Failed to get auth token for CrewAI.");
        }

        var client = this._httpClientFactory?.CreateClient() ?? new();
        client.DefaultRequestHeaders.Add("Authorization", $"Bearer {authToken}");
        client.BaseAddress = this._endpoint;
        return client;
    }

    #endregion
}

/// <summary>
/// Internal interface used for mocking and testing.
/// </summary>
internal interface ICrewAIEntepriseClient
{
    Task<CrewAIRequiredInputs> GetInputsAsync();
    Task<CrewAIKickoffResponse> KickoffAsync(
        object? inputs,
        string? taskWebhookUrl = null,
        string? stepWebhookUrl = null,
        string? crewWebhookUrl = null);
    Task<CrewAIStatusResponse> GetStatusAsync(string taskId);
}
