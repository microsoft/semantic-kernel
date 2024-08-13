// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Represents a client for interacting with the text generation through Bedrock.
/// </summary>
internal sealed class BedrockTextGenerationClient
{
    private readonly string _modelId;
    private readonly string _modelProvider;
    private readonly IAmazonBedrockRuntime _bedrockRuntime;
    private readonly IBedrockTextGenerationIOService _ioTextService;
    private readonly BedrockClientUtilities _clientUtilities;
    private Uri? _textGenerationEndpoint;
    private readonly ILogger _logger;

    /// <summary>
    /// Builds the client object and registers the model input-output service given the user's passed in model ID.
    /// </summary>
    /// <param name="modelId">The model to be used for text generation. </param>
    /// <param name="bedrockRuntime">The IAmazonBedrockRuntime object to be used for Bedrock runtime actions.</param>
    /// <param name="loggerFactory">Logger for error output.</param>
    /// <exception cref="ArgumentException"></exception>
    internal BedrockTextGenerationClient(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        var clientService = new BedrockClientIOService();
        this._modelId = modelId;
        this._bedrockRuntime = bedrockRuntime;
        this._ioTextService = clientService.GetTextIOService(modelId);
        this._modelProvider = clientService.GetModelProviderAndName(modelId).modelProvider;
        this._clientUtilities = new BedrockClientUtilities();
        this._logger = loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance;
    }

    internal async Task<IReadOnlyList<TextContent>> InvokeBedrockModelAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);
        var requestBody = this._ioTextService.GetInvokeModelRequestBody(this._modelId, prompt, executionSettings);
        var invokeRequest = new InvokeModelRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
            Body = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody))
        };
        var regionEndpoint = this._bedrockRuntime.DetermineServiceOperationEndpoint(invokeRequest).URL;
        this._textGenerationEndpoint = new Uri(regionEndpoint);
        InvokeModelResponse? response = null;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._textGenerationEndpoint, this._modelId, this._modelProvider, prompt, executionSettings);
        ActivityStatusCode activityStatus;
        try
        {
            response = await this._bedrockRuntime.InvokeModelAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
            if (activity is not null)
            {
                activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                activity.SetStatus(activityStatus);
            }
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Can't invoke with '{ModelId}'. Reason: {Error}", this._modelId, ex.Message);
            if (activity is not null)
            {
                activity.SetError(ex);
                if (response != null)
                {
                    activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                    activity.SetStatus(activityStatus);
                }
                else
                {
                    // If response is null, set a default status or leave it unset
                    activity.SetStatus(ActivityStatusCode.Error); // or ActivityStatusCode.Unset
                }
            }
            throw;
        }
        if ((response == null) || (response.Body == null))
        {
            throw new ArgumentException("Response is null");
        }
        activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
        activity?.SetStatus(activityStatus);
        IReadOnlyList<TextContent> textResponse = this._ioTextService.GetInvokeResponseBody(response);
        activity?.SetCompletionResponse(textResponse);
        return textResponse;
    }

    internal async IAsyncEnumerable<StreamingTextContent> StreamTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);
        var requestBody = this._ioTextService.GetInvokeModelRequestBody(this._modelId, prompt, executionSettings);
        var invokeRequest = new InvokeModelWithResponseStreamRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
            Body = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody))
        };
        var regionEndpoint = this._bedrockRuntime.DetermineServiceOperationEndpoint(invokeRequest).URL;
        this._textGenerationEndpoint = new Uri(regionEndpoint);
        InvokeModelWithResponseStreamResponse? streamingResponse = null;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._textGenerationEndpoint, this._modelId, this._modelProvider, prompt, executionSettings);
        ActivityStatusCode activityStatus;
        try
        {
            streamingResponse = await this._bedrockRuntime.InvokeModelWithResponseStreamAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
            if (activity is not null)
            {
                activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(streamingResponse.HttpStatusCode);
                activity.SetStatus(activityStatus);
            }
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Can't invoke with '{ModelId}'. Reason: {Error}", this._modelId, ex.Message);
            if (activity is not null)
            {
                activity.SetError(ex);
                if (streamingResponse != null)
                {
                    activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(streamingResponse.HttpStatusCode);
                    activity.SetStatus(activityStatus);
                }
                else
                {
                    // If streamingResponse is null, set a default status or leave it unset
                    activity.SetStatus(ActivityStatusCode.Error); // or ActivityStatusCode.Unset
                }
            }
            throw;
        }

        List<StreamingTextContent>? streamedContents = activity is not null ? [] : null;
        foreach (var item in streamingResponse.Body)
        {
            if (item is not PayloadPart payloadPart)
            {
                continue;
            }
            var chunk = JsonSerializer.Deserialize<JsonNode>(payloadPart.Bytes);
            if (chunk is null)
            {
                continue;
            }
            IEnumerable<string> texts = this._ioTextService.GetTextStreamOutput(chunk);
            foreach (var text in texts)
            {
                var content = new StreamingTextContent(text);
                streamedContents?.Add(content);
                yield return new StreamingTextContent(text);
            }
        }
        activity?.SetStatus(this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(streamingResponse.HttpStatusCode));
        activity?.EndStreaming(streamedContents);
    }
}
