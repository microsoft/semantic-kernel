// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal sealed class BedrockTextEmbeddingGenerationClient
{
    private readonly string _modelId;
    private readonly IBedrockTextEmbeddingService _ioVectorService;
    private readonly IAmazonBedrockRuntime _bedrockRuntime;
    private readonly ILogger _logger;

    internal BedrockTextEmbeddingGenerationClient(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        var serviceFactory = new BedrockServiceFactory();
        this._modelId = modelId;
        this._bedrockRuntime = bedrockRuntime;
        this._ioVectorService = serviceFactory.CreateTextEmbeddingService(modelId);
        this._logger = loggerFactory?.CreateLogger(this.GetType()) ?? NullLogger.Instance;
    }

    internal async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> texts,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrEmpty(texts);

        var embeddings = new List<ReadOnlyMemory<float>>();

        foreach (var item in texts)
        {
            try
            {
                var embedding = await this.GetEmbeddingForTextAsync(item, cancellationToken).ConfigureAwait(false);
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

    private async Task<ReadOnlyMemory<float>> GetEmbeddingForTextAsync(
        string text,
        CancellationToken cancellationToken = default)
    {
        var invokeRequest = new InvokeModelRequest
        {
            ModelId = this._modelId,
            Accept = "application/json",
            ContentType = "application/json",
        };

        InvokeModelResponse? response = null;

        try
        {
            var requestBody = this._ioVectorService.GetInvokeModelRequestBody(this._modelId, text);
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

        return this._ioVectorService.GetInvokeResponseBody(response);
    }
}
