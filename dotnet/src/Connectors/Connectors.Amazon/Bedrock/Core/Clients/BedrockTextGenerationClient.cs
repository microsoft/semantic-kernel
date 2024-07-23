// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Connectors.Amazon.Models.AI21;
using Connectors.Amazon.Models.Amazon;
using Connectors.Amazon.Models.Anthropic;
using Connectors.Amazon.Models.Cohere;
using Connectors.Amazon.Models.Meta;
using Connectors.Amazon.Models.Mistral;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

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
    private readonly IBedrockModelIOService<ITextGenerationRequest, ITextGenerationResponse> _ioService;

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
        string[] parts = modelId.Split('.'); //modelId looks like "amazon.titan-text-premier-v1:0"
        string modelProvider = parts[0];
        string modelName = parts.Length > 1 ? parts[1] : string.Empty;
        switch (modelProvider)
        {
            case "ai21":
                if (modelName.StartsWith("jamba", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new AI21JambaIOService();
                    break;
                }
                if (modelName.StartsWith("j2-", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new AI21JurassicIOService();
                    break;
                }
                throw new ArgumentException($"Unsupported AI21 model: {modelId}");
            case "amazon":
                if (modelName.StartsWith("titan-", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new AmazonIOService();
                    break;
                }
                throw new ArgumentException($"Unsupported Amazon model: {modelId}");
            case "anthropic":
                if (modelName.StartsWith("claude-", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new AnthropicIOService();
                    break;
                }
                throw new ArgumentException($"Unsupported Anthropic model: {modelId}");
            case "cohere":
                if (modelName.StartsWith("command-r", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new CohereCommandRIOService();
                    break;
                }
                if (modelName.StartsWith("command-", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new CohereCommandIOService();
                    break;
                }
                throw new ArgumentException($"Unsupported Cohere model: {modelId}");
            case "meta": // llama2 will be deprecated in August 2024 so not supporting
                if (modelName.StartsWith("llama3-", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new MetaIOService();
                    break;
                }
                throw new ArgumentException($"Unsupported Meta model: {modelId}");
            case "mistral":
                if (modelName.StartsWith("mistral-", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new MistralIOService();
                    break;
                }
                if (modelName.StartsWith("mixtral-", StringComparison.OrdinalIgnoreCase))
                {
                    this._ioService = new MistralIOService();
                    break;
                }
                throw new ArgumentException($"Unsupported Mistral model: {modelId}");
            default:
                throw new ArgumentException($"Unsupported model provider: {modelProvider}");
        }
    }

    private protected async Task<IReadOnlyList<TextContent>> InvokeBedrockModelAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
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
