// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Represents a text generation service using Amazon Bedrock API.
/// </summary>
public class BedrockTextGenerationService : ITextGenerationService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly BedrockTextGenerationClient _textGenerationClient;

    /// <summary>
    /// Initializes an instance of the BedrockTextGenerationService using an IAmazonBedrockRuntime object passed in by the user.
    /// </summary>
    /// <param name="modelId">The model to be used for the text generation service.</param>
    /// <param name="bedrockRuntime">The runtime object for the service.</param>
    /// <param name="loggerFactory">The logger for error logging.</param>
    public BedrockTextGenerationService(string modelId, IAmazonBedrockRuntime bedrockRuntime, ILoggerFactory? loggerFactory = null)
    {
        this._textGenerationClient = new BedrockTextGenerationClient(modelId, bedrockRuntime, loggerFactory);
        this._attributesInternal.Add(AIServiceExtensions.ModelIdKey, modelId);
    }

    /// <inheritdoc />
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;

    /// <inheritdoc />
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._textGenerationClient.InvokeBedrockModelAsync(prompt, executionSettings, cancellationToken);

    /// <inheritdoc />
    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => this._textGenerationClient.StreamTextAsync(prompt, executionSettings, kernel, cancellationToken);
}
