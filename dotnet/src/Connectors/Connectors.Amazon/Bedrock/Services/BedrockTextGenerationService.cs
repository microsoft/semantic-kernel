// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockRuntime;
using Connectors.Amazon.Core;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.TextGeneration;

namespace Connectors.Amazon.Services;

public class BedrockTextGenerationService : BedrockTextGenerationClient<ITextGenerationRequest, ITextGenerationResponse>, ITextGenerationService
{
    private readonly Dictionary<string, object?> _attributesInternal = [];
    private readonly AmazonBedrockRuntimeClient _chatCompletionClient;

    public BedrockTextGenerationService(string modelId, IAmazonBedrockRuntime bedrockApi)
        : base(modelId, bedrockApi)
    {
    }
    public BedrockTextGenerationService(string modelId)
        : base(modelId, new AmazonBedrockRuntimeClient())
    {
    }
    public IReadOnlyDictionary<string, object?> Attributes => this._attributesInternal;
    public Task<IReadOnlyList<TextContent>> GetTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => InvokeBedrockModelAsync(prompt, executionSettings, cancellationToken);

    public IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        => throw new NotImplementedException();
        // => StreamGenerateTextAsync(prompt, executionSettings, cancellationToken);
}
