// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Represents a client for interacting with the text embedding generation service through Bedrock.
/// </summary>
internal sealed class BedrockTextEmbeddingGenerationClient
{
    private readonly string _modelId;
    private readonly IBedrockCommonTextEmbeddingGenerationService _ioVectorGenerationService;
    private readonly IAmazonBedrockRuntime _bedrockRuntime;
    private readonly ILogger _logger;

    internal BedrockTextEmbeddingGenerationClient(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        var serviceFactory = new BedrockServiceFactory();
        this._modelId = modelId;
        this._bedrockRuntime = bedrockRuntime;
        this._ioVectorGenerationService = serviceFactory.CreateTextEmbeddingService(modelId);
        this._logger = loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance;
    }

    internal async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> texts,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrEmpty(texts);

        return this._ioVectorGenerationService switch
        {
            IBedrockCommonSplitTextEmbeddingGenerationService => await this.GenerateSingleEmbeddingsAsync(texts, cancellationToken).ConfigureAwait(false),
            IBedrockCommonBatchTextEmbeddingGenerationService => await this.GenerateBatchEmbeddingsAsync(texts, cancellationToken).ConfigureAwait(false),
            _ => throw new NotSupportedException("Unsupported service type")
        };
    }

    private async Task<IList<ReadOnlyMemory<float>>> GenerateSingleEmbeddingsAsync(
        IList<string> texts,
        CancellationToken cancellationToken = default
    )
    {
        var embeddings = new List<ReadOnlyMemory<float>>();
        foreach (var item in texts)
        {
            try
            {
                var embedding = await this.GetEmbeddingForSingleTextAsync(item, cancellationToken).ConfigureAwait(false);
                embeddings.Add(embedding);
            }
            catch (Exception ex)
            {
                this._logger.LogError(ex, "Can't generate embeddings for '{Text}'. Reason: {Error}", item, ex.Message);
                throw;
            }
        }

        return embeddings;
    }

    private async Task<ReadOnlyMemory<float>> GetEmbeddingForSingleTextAsync(
        string text,
        CancellationToken cancellationToken = default)
    {
        var splitVectorService = this._ioVectorGenerationService as IBedrockCommonSplitTextEmbeddingGenerationService;
        var invokeRequest = new InvokeModelRequest
        {
            ModelId = this._modelId,
            Accept = "application/json",
            ContentType = "application/json",
        };

        InvokeModelResponse? response = null;

        try
        {
            var requestBody = splitVectorService!.GetInvokeModelRequestBody(this._modelId, text);
            using var requestBodyStream = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody));
            invokeRequest.Body = requestBodyStream;

            response = await this._bedrockRuntime.InvokeModelAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Can't invoke with '{ModelId}'. Reason: {Error}", this._modelId, ex.Message);

            throw;
        }

        if ((response == null) || (response.Body == null))
        {
            throw new ArgumentException("Response is null");
        }

        return splitVectorService.GetInvokeResponseBody(response);
    }

    private async Task<IList<ReadOnlyMemory<float>>> GenerateBatchEmbeddingsAsync(
        IList<string> texts,
        CancellationToken cancellationToken = default
    )
    {
        var batchVectorService = this._ioVectorGenerationService as IBedrockCommonBatchTextEmbeddingGenerationService;
        var invokeRequest = new InvokeModelRequest
        {
            ModelId = this._modelId,
            Accept = "application/json",
            ContentType = "application/json",
        };

        InvokeModelResponse? response = null;

        try
        {
            var requestBody = batchVectorService!.GetInvokeModelRequestBody(this._modelId, texts);
            using var requestBodyStream = new MemoryStream(JsonSerializer.SerializeToUtf8Bytes(requestBody));
            invokeRequest.Body = requestBodyStream;

            response = await this._bedrockRuntime.InvokeModelAsync(invokeRequest, cancellationToken).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Can't invoke with '{ModelId}'. Reason: {Error}", this._modelId, ex.Message);
            throw;
        }

        if (response?.Body == null)
        {
            throw new ArgumentException("Response is null");
        }

        return batchVectorService.GetInvokeResponseBody(response);
    }
}
