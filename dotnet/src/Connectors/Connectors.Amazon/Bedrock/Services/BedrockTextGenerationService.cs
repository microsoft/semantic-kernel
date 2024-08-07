// Copyright (c) Microsoft. All rights reserved.

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
    /// <param name="modelId"></param>
    /// <param name="bedrockApi"></param>
    /// <param name="loggerFactory"></param>
    public BedrockTextGenerationService(string modelId, IAmazonBedrockRuntime bedrockApi, ILoggerFactory? loggerFactory = null)
    {
        this._textGenerationClient = new BedrockTextGenerationClient(modelId, bedrockApi, loggerFactory);
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
