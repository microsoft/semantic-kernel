// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextClassification;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text classification service.
/// </summary>
public sealed class OpenAITextClassificationService : ITextClassification
{
    private readonly Dictionary<string, object?> _attributes = new();

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributes;

    /// <summary>
    /// Create an instance of the OpenAI text classification service connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public OpenAITextClassificationService(
        string modelId,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        throw new NotImplementedException();

        this._attributes.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc />
    public Task<ClassificationContent> ClassifyTextAsync(
        string text,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }
}
