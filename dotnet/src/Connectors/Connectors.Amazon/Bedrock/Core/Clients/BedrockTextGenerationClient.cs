// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Bedrock.Core;
using Connectors.Amazon.Models;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Bedrock.Core;

/// <summary>
/// Represents a client for interacting with the text generation through Bedrock.
/// </summary>
internal sealed class BedrockTextGenerationClient
{
    private readonly string _modelId;
    private readonly string _modelProvider;
    private readonly IAmazonBedrockRuntime _bedrockApi;
    private readonly IBedrockModelIOService _ioService;
    private readonly BedrockClientUtilities _clientUtilities;
    private Uri? _textGenerationEndpoint;

    /// <summary>
    /// Builds the client object and registers the model input-output service given the user's passed in model ID.
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="bedrockApi"></param>
    /// <exception cref="ArgumentException"></exception>
    public BedrockTextGenerationClient(string modelId, IAmazonBedrockRuntime bedrockApi)
    {
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        this._ioService = new BedrockClientIOService().GetIOService(modelId);
        this._modelProvider = new BedrockClientIOService().GetModelProvider(modelId);
        this._clientUtilities = new BedrockClientUtilities();
    }

    internal async Task<IReadOnlyList<TextContent>> InvokeBedrockModelAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(prompt);
        var requestBody = this._ioService.GetInvokeModelRequestBody(this._modelId, prompt, executionSettings);
        var invokeRequest = new InvokeModelRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
            Body = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody))
        };
        var regionEndpoint = this._bedrockApi.DetermineServiceOperationEndpoint(invokeRequest).URL;
        this._textGenerationEndpoint = new Uri(regionEndpoint);
        InvokeModelResponse? response = null;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._textGenerationEndpoint, this._modelId, this._modelProvider, prompt, executionSettings);
        ActivityStatusCode activityStatus;
        try
        {
            response = await this._bedrockApi.InvokeModelAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            if (response != null)
            {
                activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
                activity.SetStatus(activityStatus);
            }

            throw;
        }
        activityStatus = this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(response.HttpStatusCode);
        activity?.SetStatus(activityStatus);
        IReadOnlyList<TextContent> textResponse = this._ioService.GetInvokeResponseBody(response);
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
        var requestBody = this._ioService.GetInvokeModelRequestBody(this._modelId, prompt, executionSettings);
        var invokeRequest = new InvokeModelWithResponseStreamRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
            Body = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody))
        };
        var regionEndpoint = this._bedrockApi.DetermineServiceOperationEndpoint(invokeRequest).URL;
        this._textGenerationEndpoint = new Uri(regionEndpoint);
        InvokeModelWithResponseStreamResponse? streamingResponse = null;
        using var activity = ModelDiagnostics.StartCompletionActivity(
            this._textGenerationEndpoint, this._modelId, this._modelProvider, prompt, executionSettings);
        try
        {
            streamingResponse = await this._bedrockApi.InvokeModelWithResponseStreamAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            if (streamingResponse != null)
            {
                activity.SetStatus(this._clientUtilities.ConvertHttpStatusCodeToActivityStatusCode(streamingResponse.HttpStatusCode));
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
            IEnumerable<string> texts = this._ioService.GetTextStreamOutput(chunk);
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
