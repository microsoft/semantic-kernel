// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Contains result after prompt rendering process.
/// </summary>
internal sealed class PromptRenderingResult
{
    public IAIService AIService { get; set; }

    public string RenderedPrompt { get; set; }

    public PromptExecutionSettings? ExecutionSettings { get; set; }

#pragma warning disable CS0618 // Events are deprecated
    public PromptRenderedEventArgs? RenderedEventArgs { get; set; }
#pragma warning restore CS0618 // Events are deprecated

    public PromptRenderedContext? RenderedContext { get; set; }

    public PromptRenderingResult(IAIService aiService, string renderedPrompt)
    {
        this.AIService = aiService;
        this.RenderedPrompt = renderedPrompt;
    }
}
