// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
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
    private readonly IBedrockTextGenerationService _ioTextService;
    private Uri? _textGenerationEndpoint;
    private readonly ILogger _logger;

    /// <summary>
    /// Builds the client object and registers the model input-output service given the user's passed in model ID.
    /// </summary>
    /// <param name="modelId">The model to be used for text generation. </param>
    /// <param name="bedrockRuntime">The <see cref="IAmazonBedrockRuntime"/> instance to be used for Bedrock runtime actions.</param>
    /// <param name="loggerFactory">Logger for error output.</param>
    internal BedrockTextGenerationClient(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        var serviceFactory = new BedrockServiceFactory();
        this._modelId = modelId;
        this._bedrockRuntime = bedrockRuntime;
        this._ioTextService = serviceFactory.CreateTextGenerationService(modelId);
        this._modelProvider = serviceFactory.GetModelProviderAndName(modelId).modelProvider;
        this._logger = loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Generates a chat message based on the provided chat history and execution settings.
    /// </summary>
    /// <param name="prompt">The prompt for generating the text.</param>
    /// <param name="executionSettings">The execution settings for the text generation.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The generated text.</returns>///
    /// <exception cref="ArgumentNullException">Thrown when the chat history is null.</exception>
    /// <exception cref="ArgumentException">Thrown when the chat is empty.</exception>
    /// <exception cref="InvalidOperationException">Thrown when response content is not available.</exception>
    internal async Task<IReadOnlyList<TextContent>> InvokeBedrockModelAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);
        var invokeRequest = new InvokeModelRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
        };
        var regionEndpoint = this._bedrockRuntime.DetermineServiceOperationEndpoint(invokeRequest).URL;
        this._textGenerationEndpoint = new Uri(regionEndpoint);
        InvokeModelResponse? response = null;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._textGenerationEndpoint, this._modelId, this._modelProvider, prompt, executionSettings);
        ActivityStatusCode activityStatus;
        try
        {
            var requestBody = this._ioTextService.GetInvokeModelRequestBody(this._modelId, prompt, executionSettings);
            using var requestBodyStream = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody));
            invokeRequest.Body = requestBodyStream;

            response = await this._bedrockRuntime.InvokeModelAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
            if (activity is not null)
            {
                activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
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
                    activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
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
        activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
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
                activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(streamingResponse.HttpStatusCode);
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
                    activityStatus = BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(streamingResponse.HttpStatusCode);
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

            foreach (var streamingContent in this._ioTextService.GetTextStreamOutput(chunk))
            {
                streamedContents?.Add(streamingContent);
                yield return streamingContent;
            }
        }
        activity?.SetStatus(BedrockClientUtilities.ConvertHttpStatusCodeToActivityStatusCode(streamingResponse.HttpStatusCode));
        activity?.EndStreaming(streamedContents);
    }
}
