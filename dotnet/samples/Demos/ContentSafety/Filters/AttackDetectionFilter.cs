// Copyright (c) Microsoft. All rights reserved.

using ContentSafety.Exceptions;
using ContentSafety.Services.PromptShield;
using Microsoft.SemanticKernel;

namespace ContentSafety.Filters;

/// <summary>
/// This filter performs attack detection using Azure AI Content Safety - Prompt Shield service.
/// For more information: https://learn.microsoft.com/en-us/azure/ai-services/content-safety/quickstart-jailbreak
/// </summary>
public class AttackDetectionFilter(PromptShieldService promptShieldService) : IPromptRenderFilter
{
    private readonly PromptShieldService _promptShieldService = promptShieldService;

    public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
    {
        // Running prompt rendering operation
        await next(context);

        // Getting rendered prompt
        var prompt = context.RenderedPrompt;

        // Getting documents data from kernel
        var documents = context.Arguments["documents"] as List<string>;

        // Calling Prompt Shield service for attack detection
        var response = await this._promptShieldService.DetectAttackAsync(new PromptShieldRequest
        {
            UserPrompt = prompt!,
            Documents = documents
        });

        var attackDetected =
            response.UserPromptAnalysis?.AttackDetected is true ||
            response.DocumentsAnalysis?.Any(l => l.AttackDetected) is true;

        if (attackDetected)
        {
            throw new AttackDetectionException("Attack detected. Operation is denied.")
            {
                UserPromptAnalysis = response.UserPromptAnalysis,
                DocumentsAnalysis = response.DocumentsAnalysis
            };
        }
    }
}
