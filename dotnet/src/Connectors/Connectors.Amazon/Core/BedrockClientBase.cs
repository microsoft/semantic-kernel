// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal sealed class BedrockClientBase<TRequest, TResponse>
{
    private const string ModelProvider = "amazon";
    private readonly string _modelId;
    private readonly IAmazonBedrockRuntime _bedrockApi;
    private readonly IBedrockModelIoService<TRequest, TResponse> _ioService;

    public BedrockClientBase(string modelId, IAmazonBedrockRuntime bedrockApi, IBedrockModelIoService<TRequest, TResponse> ioService)
    {
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        this._ioService = ioService;
    }
    internal async Task<TResponse> InvokeBedrockModelAsync(string prompt, PromptExecutionSettings executionSettings, CancellationToken cancellationToken = default)
    {
        var requestBody = this._ioService.GetApiRequestBody(prompt, executionSettings);
        var invokeRequest = new InvokeModelRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
            Body = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody))
        };
        var response = await this._bedrockApi.InvokeModelAsync(invokeRequest, cancellationToken).ConfigureAwait(true);
        return this._ioService.ConvertApiResponse(response.Body);
    }
    internal async Task<TResponse> ConverseBedrockModelAsync(string prompt, PromptExecutionSettings executionSettings, CancellationToken cancellationToken = default)
    {
        var requestBody = this._ioService.GetApiRequestBody(prompt, executionSettings);
        var converseRequest = new ConverseRequest();
        var response = await this._bedrockApi.ConverseAsync(converseRequest, cancellationToken).ConfigureAwait(true);
        return this._ioService.ConvertApiResponse(response.Body);
    }
    internal async Task<IReadOnlyList<ChatMessageContent>> GenerateChatMessageAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        IChatCompletionResponse bedrockResponse;
        TResponse responses;
        using var activity = ModelDiagnostics.StartCompletionActivity(this._modelId, ModelProvider, chatHistory, executionSettings);
        try
        {
            responses = await this.InvokeBedrockModelAsync(chatHistory.ToString(), executionSettings ?? new PromptExecutionSettings(), cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex) when (activity is not null)
        {
            activity.SetError(ex);
            throw;
        }
        return activity.SetCompletionResponse();
    }
}
