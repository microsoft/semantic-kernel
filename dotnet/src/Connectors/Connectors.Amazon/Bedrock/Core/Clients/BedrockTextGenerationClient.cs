// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.EventStreams;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Connectors.Amazon.Models.AI21;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Models.Anthropic;
using Connectors.Amazon.Models.Cohere;
using Connectors.Amazon.Models.Meta;
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
            case "cohere":
                if (modelId.Contains("command-r"))
                {
                    this._ioService = new CohereCommandRIoService();
                }
                else if (modelId.Contains("command"))
                {
                    this._ioService = new CohereCommandIoService();
                }
                else
                {
                    throw new ArgumentException($"Unsupported Cohere model: {modelId}");
                }
                break;
            case "meta":
                this._ioService = new LlamaIoService();
                break;
            default:
                throw new ArgumentException($"Unsupported model provider: {modelProvider}");
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

    private protected async IAsyncEnumerable<StreamingTextContent> StreamTextAsync(string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var requestBody = this._ioService.GetInvokeModelRequestBody(prompt, executionSettings);
        var invokeRequest = new InvokeModelWithResponseStreamRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
            Body = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody))
        };
        InvokeModelWithResponseStreamResponse streamingResponse = null;
        try
        {
            // Send the request to the Bedrock Runtime and wait for the response.
            streamingResponse = await this._bedrockApi.InvokeModelWithResponseStreamAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
        }
        catch (AmazonBedrockRuntimeException e)
        {
            Console.WriteLine($"ERROR: Can't invoke '{this._modelId}'. Reason: {e.Message}");
            throw;
        }

        foreach (var item in streamingResponse.Body)
        {
            var chunk = JsonSerializer.Deserialize<JsonNode>((item as PayloadPart).Bytes);
            IEnumerable<string> texts = this._ioService.GetTextStreamOutput(chunk);
            foreach (var text in texts)
            {
                yield return new StreamingTextContent(text);
            }
        }
    }
}
