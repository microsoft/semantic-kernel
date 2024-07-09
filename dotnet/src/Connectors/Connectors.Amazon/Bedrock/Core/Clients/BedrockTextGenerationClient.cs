// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Connectors.Amazon.Models.AI21;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Models.Anthropic;
using Connectors.Amazon.Models.Mistral;
using Microsoft.SemanticKernel;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

public abstract class BedrockTextGenerationClient<TRequest, TResponse>
    where TRequest : ITextGenerationRequest
    where TResponse : ITextGenerationResponse
{
    private readonly string _modelId;
    private readonly IAmazonBedrockRuntime _bedrockApi;
    private readonly IBedrockModelIoService<ITextGenerationRequest, ITextGenerationResponse> _ioService;

    protected BedrockTextGenerationClient(string modelId, IAmazonBedrockRuntime bedrockApi)
    {
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        int periodIndex = modelId.IndexOf('.'); //modelId looks like "amazon.titan-embed-text-v1"
        string modelProvider = periodIndex >= 0 ? modelId.Substring(0, periodIndex) : modelId;
        switch (modelProvider)
        {
            case "amazon":
                this._ioService = new AmazonIoService();
                break;
            case "mistral":
                this._ioService = new MistralIoService();
                break;
            case "ai21":
                this._ioService = new AI21IoService();
                break;
            case "anthropic":
                this._ioService = new AnthropicIoService();
                break;
            default:
                throw new Exception("Error: model not found");
                break;
        }
    }

    private protected async Task<IReadOnlyList<TextContent>> InvokeBedrockModelAsync(string prompt, PromptExecutionSettings executionSettings, CancellationToken cancellationToken = default)
    {
        var requestBody = this._ioService.GetInvokeModelRequestBody(prompt, executionSettings);
        var invokeRequest = new InvokeModelRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
            Body = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody))
        };
        var response = await this._bedrockApi.InvokeModelAsync(invokeRequest, cancellationToken).ConfigureAwait(true);
        return this._ioService.GetInvokeResponseBody(response);
    }
}
