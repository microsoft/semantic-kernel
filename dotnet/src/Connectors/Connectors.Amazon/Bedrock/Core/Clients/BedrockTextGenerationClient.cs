// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Bedrock.Core;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Bedrock.Core;

/// <summary>
/// Represents a client for interacting with the text generation through Bedrock.
/// </summary>
/// <typeparam name="TRequest"> Request object which is an ITextGenerationRequest. </typeparam>
/// <typeparam name="TResponse"> Response object which is an ITextGenerationResponse. </typeparam>
public abstract class BedrockTextGenerationClient<TRequest, TResponse>
    where TRequest : ITextGenerationRequest
    where TResponse : ITextGenerationResponse
{
    private readonly string _modelId;
    private readonly IAmazonBedrockRuntime _bedrockApi;
    private readonly IBedrockModelIOService _ioService;

    /// <summary>
    /// Builds the client object and registers the model input-output service given the user's passed in model ID.
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="bedrockApi"></param>
    /// <exception cref="ArgumentException"></exception>
    protected BedrockTextGenerationClient(string modelId, IAmazonBedrockRuntime bedrockApi)
    {
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        this._ioService = new BedrockClientIOService().GetIOService(modelId);
    }

    private protected async Task<IReadOnlyList<TextContent>> InvokeBedrockModelAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        var requestBody = this._ioService.GetInvokeModelRequestBody(this._modelId, prompt, executionSettings);
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
        var requestBody = this._ioService.GetInvokeModelRequestBody(this._modelId, prompt, executionSettings);
        var invokeRequest = new InvokeModelWithResponseStreamRequest
        {
            ModelId = this._modelId,
            Accept = "*/*",
            ContentType = "application/json",
            Body = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody))
        };
        InvokeModelWithResponseStreamResponse streamingResponse;
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
