// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.ContentSafety;
using ContentSafety.Exceptions;
using Microsoft.SemanticKernel;

namespace ContentSafety.Filters;

/// <summary>
/// This filter performs text moderation using Azure AI Content Safety service.
/// For more information: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-text
/// </summary>
public class TextModerationFilter(
    ContentSafetyClient contentSafetyClient,
    ILogger<TextModerationFilter> logger) : IPromptRenderFilter
{
    private readonly ContentSafetyClient _contentSafetyClient = contentSafetyClient;
    private readonly ILogger<TextModerationFilter> _logger = logger;

    public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
    {
        // Running prompt rendering operation
        await next(context);

        var prompt = context.RenderedPrompt;
        this._logger.LogInformation("Rendered prompt: {RenderedPrompt}", prompt);

        // Running Azure AI Content Safety text analysis
        var analysisResult = (await this._contentSafetyClient.AnalyzeTextAsync(new AnalyzeTextOptions(prompt))).Value;

        var highSeverity = false;

        foreach (var analysis in analysisResult.CategoriesAnalysis)
        {
            this._logger.LogInformation("Category: {Category}. Severity: {Severity}", analysis.Category, analysis.Severity);

            if (analysis.Severity > 0)
            {
                highSeverity = true;
            }
        }

        if (highSeverity)
        {
            throw new TextModerationException("Offensive content detected. Operation is denied.");
        }
    }
}
