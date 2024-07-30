// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Bedrock.Core;
using Connectors.Amazon.Models;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Bedrock.Core;

/// <summary>
/// Represents a client for interacting with the text generation through Bedrock.
/// </summary>
internal sealed class BedrockTextGenerationClient
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
    public BedrockTextGenerationClient(string modelId, IAmazonBedrockRuntime bedrockApi)
    {
        this._modelId = modelId;
        this._bedrockApi = bedrockApi;
        this._ioService = new BedrockClientIOService().GetIOService(modelId);
    }

    internal async Task<IReadOnlyList<TextContent>> InvokeBedrockModelAsync(
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
        var response = await this._bedrockApi.InvokeModelAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
        return this._ioService.GetInvokeResponseBody(response);
    }

    internal async IAsyncEnumerable<StreamingTextContent> StreamTextAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
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
            streamingResponse = await this._bedrockApi.InvokeModelWithResponseStreamAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
        }
        catch (AmazonBedrockRuntimeException e)
        {
            Console.WriteLine($"ERROR: Can't invoke '{this._modelId}'. Reason: {e.Message}");
            throw;
        }

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
                yield return new StreamingTextContent(text);
            }
        }
    }
}
