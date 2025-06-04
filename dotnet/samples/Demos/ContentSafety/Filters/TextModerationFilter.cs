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

        // Getting rendered prompt
        var prompt = context.RenderedPrompt;

        // Running Azure AI Content Safety text analysis
        var analysisResult = (await this._contentSafetyClient.AnalyzeTextAsync(new AnalyzeTextOptions(prompt))).Value;

        this.ProcessTextAnalysis(analysisResult);
    }

    /// <summary>
    /// Processes text analysis result.
    /// Content Safety recognizes four distinct categories of objectionable content: Hate, Sexual, Violence, Self-Harm.
    /// Every harm category the service applies also comes with a severity level rating.
    /// The severity level is meant to indicate the severity of the consequences of showing the flagged content.
    /// Full severity scale: 0 to 7.
    /// Trimmed severity scale: 0, 2, 4, 6.
    /// More information here:
    /// https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/harm-categories#harm-categories
    /// https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/harm-categories#severity-levels
    /// </summary>
    private void ProcessTextAnalysis(AnalyzeTextResult analysisResult)
    {
        var highSeverity = false;
        var analysisDetails = new Dictionary<TextCategory, int>();

        foreach (var analysis in analysisResult.CategoriesAnalysis)
        {
            this._logger.LogInformation("Category: {Category}. Severity: {Severity}", analysis.Category, analysis.Severity);

            if (analysis.Severity > 0)
            {
                highSeverity = true;
            }

            analysisDetails.Add(analysis.Category, analysis.Severity ?? 0);
        }

        if (highSeverity)
        {
            throw new TextModerationException("Offensive content detected. Operation is denied.")
            {
                CategoriesAnalysis = analysisDetails
            };
        }
    }
}
