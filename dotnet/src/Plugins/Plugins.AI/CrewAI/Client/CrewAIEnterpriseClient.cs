// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI;

/// <summary>
/// Internal interface used for mocking and testing.
/// </summary>
internal interface ICrewAIEnterpriseClient
{
    Task<CrewAIRequiredInputs> GetInputsAsync(CancellationToken cancellationToken = default);
    Task<CrewAIKickoffResponse> KickoffAsync(
        object? inputs,
        string? taskWebhookUrl = null,
        string? stepWebhookUrl = null,
        string? crewWebhookUrl = null,
        CancellationToken cancellationToken = default);
    Task<CrewAIStatusResponse> GetStatusAsync(string taskId, CancellationToken cancellationToken = default);
}

/// <summary>
/// A client for interacting with the CrewAI Enterprise API.
/// </summary>
internal class CrewAIEnterpriseClient : ICrewAIEnterpriseClient
{
    private readonly Uri _endpoint;
    private readonly Func<Task<string>> _authTokenProvider;
    private readonly IHttpClientFactory? _httpClientFactory;

    public CrewAIEnterpriseClient(Uri endpoint, Func<Task<string>> authTokenProvider, IHttpClientFactory? clientFactory = null)
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
    /// <param name="cancellationToken">A <see cref="CancellationToken"/></param>
    /// <returns>Aninstance of <see cref="CrewAIRequiredInputs"/> describing the required inputs.</returns>
    /// <exception cref="KernelException"></exception>
    public async Task<CrewAIRequiredInputs> GetInputsAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            using var client = await this.CreateHttpClientAsync().ConfigureAwait(false);
            using var requestMessage = HttpRequest.CreateGetRequest("/inputs");
            using var response = await client.SendWithSuccessCheckAsync(requestMessage, cancellationToken)
                .ConfigureAwait(false);

            var body = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken)
                .ConfigureAwait(false);

            var requirements = JsonSerializer.Deserialize<CrewAIRequiredInputs>(body);

            return requirements ?? throw new KernelException(message: $"Failed to deserialize requirements from CrewAI. Response: {body}");
        }
        catch (Exception ex) when (ex is not KernelException)
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
    /// <param name="cancellationToken">A <see cref="CancellationToken"/></param>
    /// <returns>A string containing the Id of the started Crew Task.</returns>
    public async Task<CrewAIKickoffResponse> KickoffAsync(
        object? inputs,
        string? taskWebhookUrl = null,
        string? stepWebhookUrl = null,
        string? crewWebhookUrl = null,
        CancellationToken cancellationToken = default)
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
            using var requestMessage = HttpRequest.CreatePostRequest("/kickoff", content);
            using var response = await client.SendWithSuccessCheckAsync(requestMessage, cancellationToken)
                .ConfigureAwait(false);

            var body = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken)
                .ConfigureAwait(false);

            var kickoffResponse = JsonSerializer.Deserialize<CrewAIKickoffResponse>(body);
            return kickoffResponse ?? throw new KernelException(message: $"Failed to deserialize kickoff response from CrewAI. Response: {body}");
        }
        catch (Exception ex) when (ex is not KernelException)
        {
            throw new KernelException(message: "Failed to kickoff CrewAI Crew.", innerException: ex);
        }
    }

    /// <summary>
    /// Get the status of the Crew Task.
    /// </summary>
    /// <param name="taskId">The Id of the task.</param>
    /// <param name="cancellationToken">A <see cref="CancellationToken"/></param>
    /// <returns>A string containing the status or final result of the Crew task.</returns>
    /// <exception cref="KernelException"></exception>
    public async Task<CrewAIStatusResponse> GetStatusAsync(string taskId, CancellationToken cancellationToken = default)
    {
        try
        {
            using var client = await this.CreateHttpClientAsync().ConfigureAwait(false);
            using var requestMessage = HttpRequest.CreateGetRequest($"/status/{taskId}");
            using var response = await client.SendWithSuccessCheckAsync(requestMessage, cancellationToken)
                .ConfigureAwait(false);

            var body = await response.Content.ReadAsStringWithExceptionMappingAsync(cancellationToken)
                .ConfigureAwait(false);

            var statusResponse = JsonSerializer.Deserialize<CrewAIStatusResponse>(body);

            return statusResponse ?? throw new KernelException(message: $"Failed to deserialize status response from CrewAI. Response: {body}");
        }
        catch (Exception ex) when (ex is not KernelException)
        {
            throw new KernelException(message: "Failed to status of CrewAI Crew.", innerException: ex);
        }
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
