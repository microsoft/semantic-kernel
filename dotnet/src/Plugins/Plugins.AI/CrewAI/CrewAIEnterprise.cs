// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI;

/// <summary>
/// A plugin for interacting with the a CrewAI Crew via the Enterprise APIs.
/// </summary>
public class CrewAIEnterprise
{
    private readonly ICrewAIEnterpriseClient _crewClient;
    private readonly ILogger _logger;
    private readonly TimeSpan _pollingInterval;

    /// <summary>
    /// The name of the kickoff function.
    /// </summary>
    public const string KickoffFunctionName = "KickoffCrew";

    /// <summary>
    /// The name of the kickoff and wait function.
    /// </summary>
    public const string KickoffAndWaitFunctionName = "KickoffAndWait";

    /// <summary>
    /// Initializes a new instance of the <see cref="CrewAIEnterprise"/> class.
    /// </summary>
    /// <param name="endpoint">The base URI of the CrewAI Crew</param>
    /// <param name="authTokenProvider"> Optional provider for auth token generation. </param>
    /// <param name="httpClientFactory">The HTTP client factory. </param>
    /// <param name="loggerFactory">The logger factory. </param>
    /// <param name="pollingInterval">Defines the delay time between status calls when pollin for a kickoff to complete.</param>
    public CrewAIEnterprise(Uri endpoint, Func<Task<string>> authTokenProvider, IHttpClientFactory? httpClientFactory = null, ILoggerFactory? loggerFactory = null, TimeSpan? pollingInterval = default)
    {
        Verify.NotNull(endpoint, nameof(endpoint));
        Verify.NotNull(authTokenProvider, nameof(authTokenProvider));

        this._crewClient = new CrewAIEnterpriseClient(endpoint, authTokenProvider, httpClientFactory);
        this._logger = loggerFactory?.CreateLogger(typeof(CrewAIEnterprise)) ?? NullLogger.Instance;
        this._pollingInterval = pollingInterval ?? TimeSpan.FromSeconds(1);
    }

    /// <summary>
    /// Internal constructor used for testing purposes.
    /// </summary>
    internal CrewAIEnterprise(ICrewAIEnterpriseClient crewClient, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(crewClient, nameof(crewClient));
        this._crewClient = crewClient;
        this._logger = loggerFactory?.CreateLogger(typeof(CrewAIEnterprise)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Kicks off (starts) a CrewAI Crew with the given inputs and callbacks.
    /// </summary>
    /// <param name="inputs">An object containing key value pairs matching the required inputs of the Crew.</param>
    /// <param name="taskWebhookUrl">The task level webhook Uri.</param>
    /// <param name="stepWebhookUrl">The step level webhook Uri.</param>
    /// <param name="crewWebhookUrl">The crew level webhook Uri.</param>
    /// <returns>The Id of the scheduled kickoff.</returns>
    /// <exception cref="KernelException"></exception>
    public async Task<string> KickoffAsync(
        object? inputs,
        Uri? taskWebhookUrl = null,
        Uri? stepWebhookUrl = null,
        Uri? crewWebhookUrl = null)
    {
        try
        {
            CrewAIKickoffResponse kickoffTask = await this._crewClient.KickoffAsync(
                inputs: inputs,
                taskWebhookUrl: taskWebhookUrl?.AbsoluteUri,
                stepWebhookUrl: stepWebhookUrl?.AbsoluteUri,
                crewWebhookUrl: crewWebhookUrl?.AbsoluteUri)
                .ConfigureAwait(false);

            this._logger.LogInformation("CrewAI Crew kicked off with Id: {KickoffId}", kickoffTask.KickoffId);
            return kickoffTask.KickoffId;
        }
        catch (Exception ex)
        {
            throw new KernelException(message: "Failed to kickoff CrewAI Crew.", innerException: ex);
        }
    }

    /// <summary>
    /// Gets the current status of the CrewAI Crew kickoff.
    /// </summary>
    /// <param name="kickoffId">The Id of the Crew kickoff.</param>
    /// <returns>A <see cref="CrewAIStatusResponse"/></returns>
    /// <exception cref="KernelException"></exception>"
    [KernelFunction]
    [Description("Gets the current status of the CrewAI Crew kickoff.")]
    public async Task<CrewAIStatusResponse> GetCrewKickoffStatusAsync([Description("The Id of the kickoff")] string kickoffId)
    {
        Verify.NotNullOrWhiteSpace(kickoffId, nameof(kickoffId));

        try
        {
            CrewAIStatusResponse statusResponse = await this._crewClient.GetStatusAsync(kickoffId).ConfigureAwait(false);

            this._logger.LogInformation("CrewAI Crew status for kickoff Id: {KickoffId} is {Status}", kickoffId, statusResponse.State);
            return statusResponse;
        }
        catch (Exception ex)
        {
            throw new KernelException(message: $"Failed to get status of CrewAI Crew with kickoff Id: {kickoffId}.", innerException: ex);
        }
    }

    /// <summary>
    /// Waits for the Crew kickoff to complete and returns the result.
    /// </summary>
    /// <param name="kickoffId">The Id of the crew kickoff.</param>
    /// <returns>The result of the Crew kickoff.</returns>
    /// <exception cref="KernelException"></exception>
    [KernelFunction]
    [Description("Waits for the Crew kickoff to complete and returns the result.")]
    public async Task<string> WaitForCrewCompletionAsync([Description("The Id of the kickoff")] string kickoffId)
    {
        Verify.NotNullOrWhiteSpace(kickoffId, nameof(kickoffId));

        try
        {
            CrewAIStatusResponse? statusResponse = null;
            var status = CrewAIKickoffState.Pending;
            do
            {
                this._logger.LogInformation("Waiting for CrewAI Crew with kickoff Id: {KickoffId} to complete. Current state: {Status}", kickoffId, status);
                await Task.Delay(TimeSpan.FromSeconds(1)).ConfigureAwait(false);
                statusResponse = await this._crewClient.GetStatusAsync(kickoffId).ConfigureAwait(false);
                status = statusResponse.State;
            }
            while (!this.IsTerminalState(status));

            this._logger.LogInformation("CrewAI Crew with kickoff Id: {KickoffId} completed with status: {Status}", kickoffId, statusResponse.State);

            return status switch
            {
                CrewAIKickoffState.Failed => throw new KernelException(message: $"CrewAI Crew failed with error: {statusResponse.Result}"),
                CrewAIKickoffState.Success => statusResponse.Result ?? string.Empty,
                _ => throw new KernelException(message: "Failed to parse unexpected response from CrewAI status response."),
            };
        }
        catch (Exception ex)
        {
            throw new KernelException(message: $"Failed to wait for completion of CrewAI Crew with kickoff Id: {kickoffId}.", innerException: ex);
        }
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> that can be used to invoke the CrewAI Crew.
    /// </summary>
    /// <param name="name">The name of the <see cref="KernelFunction"/></param>
    /// <param name="description">The description of the <see cref="KernelFunction"/></param>
    /// <param name="inputMetadata">The definitions of the Crew's required inputs.</param>
    /// <param name="taskWebhookUrl">The task level webhook Uri</param>
    /// <param name="stepWebhookUrl">The step level webhook Uri</param>
    /// <param name="crewWebhookUrl">The crew level webhook Uri</param>
    /// <returns>A <see cref="KernelFunction"/> that can invoke the Crew.</returns>
    /// <exception cref="KernelException"></exception>
    public KernelPlugin CreateKernelPlugin(
        string name,
        string description,
        IEnumerable<CrewAIInputMetadata>? inputMetadata,
        Uri? taskWebhookUrl = null,
        Uri? stepWebhookUrl = null,
        Uri? crewWebhookUrl = null)
    {
        var options = new KernelFunctionFromMethodOptions()
        {
            Parameters = inputMetadata?.Select(i => new KernelParameterMetadata(i.Name) { Description = i.Description, IsRequired = true, ParameterType = i.Type }) ?? [],
            ReturnParameter = new() { ParameterType = typeof(string) },
        };

        // Define the kernel function implementation for kickoff
        [KernelFunction(KickoffFunctionName)]
        [Description("kicks off the CrewAI Crew and returns the Id of the scheduled kickoff.")]
        async Task<string> KickoffAsync(KernelArguments arguments)
        {
            Dictionary<string, object?> args = BuildArguments(inputMetadata, arguments);

            return await this.KickoffAsync(
                inputs: args,
                taskWebhookUrl: taskWebhookUrl,
                stepWebhookUrl: stepWebhookUrl,
                crewWebhookUrl: crewWebhookUrl)
                .ConfigureAwait(false);
        }

        // Define the kernel function implementation for kickoff and wait for result
        [KernelFunction(KickoffAndWaitFunctionName)]
        [Description("kicks off the CrewAI Crew, waits for it to complete, and returns the result.")]
        async Task<string> KickoffAndWaitAsync(KernelArguments arguments)
        {
            Dictionary<string, object?> args = BuildArguments(inputMetadata, arguments);

            var kickoffId = await this.KickoffAsync(
                inputs: args,
                taskWebhookUrl: taskWebhookUrl,
                stepWebhookUrl: stepWebhookUrl,
                crewWebhookUrl: crewWebhookUrl)
                .ConfigureAwait(false);

            return await this.WaitForCrewCompletionAsync(kickoffId).ConfigureAwait(false);
        }

        return KernelPluginFactory.CreateFromFunctions(
            name,
            description,
            [
                KernelFunctionFactory.CreateFromMethod(KickoffAsync, new(), options),
                KernelFunctionFactory.CreateFromMethod(KickoffAndWaitAsync, new(), options),
                KernelFunctionFactory.CreateFromMethod(this.GetCrewKickoffStatusAsync),
                KernelFunctionFactory.CreateFromMethod(this.WaitForCrewCompletionAsync)
            ]);
    }

    #region Private Methods

    /// <summary>
    /// Determines if the Crew kikoff state is terminal.
    /// </summary>
    /// <param name="state">The state of the crew kickoff</param>
    /// <returns>A <see cref="bool"/> indicating if the state is a terminal state.</returns>
    private bool IsTerminalState(CrewAIKickoffState state)
    {
        return state == CrewAIKickoffState.Failed || state == CrewAIKickoffState.Failure || state == CrewAIKickoffState.Success || state == CrewAIKickoffState.NotFound;
    }

    private static Dictionary<string, object?> BuildArguments(IEnumerable<CrewAIInputMetadata>? inputMetadata, KernelArguments arguments)
    {
        // Extract the required arguments from the KernelArguments by name
        Dictionary<string, object?> args = [];
        if (inputMetadata is not null)
        {
            foreach (var input in inputMetadata)
            {
                // If a required argument is missing, throw an exception
                if (!arguments.TryGetValue(input.Name, out object? value) || value is null || value is not string strValue)
                {
                    throw new KernelException(message: $"Missing required input '{input.Name}' for CrewAI.");
                }

                // Since this KernelFunction does not have explicit parameters all the relevant inputs are passed as strings.
                // We need to convert the inputs to the expected types.
                if (input.Type == typeof(string))
                {
                    args.Add(input.Name, value);
                }
                else
                {
                    // Try to get a converter for the input type
                    var converter = TypeConverterFactory.GetTypeConverter(input.Type);
                    if (converter is not null)
                    {
                        args.Add(input.Name, converter.ConvertFrom(value));
                    }
                    else
                    {
                        // Try to deserialize the input as a JSON object
                        var objValue = JsonSerializer.Deserialize(strValue, input.Type);
                        args.Add(input.Name, objValue);
                    }
                }
            }
        }

        return args;
    }

    #endregion
}
