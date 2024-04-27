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

        var prompt = context.RenderedPrompt;

        // Calling Prompt Shield service for attack detection
        var attackDetected = await this._promptShieldService.DetectAttackAsync(new PromptShieldRequest
        {
            UserPrompt = prompt!
        });

        if (attackDetected)
        {
            throw new AttackDetectionException("Attack detected. Operation is denied.");
        }
    }
}
