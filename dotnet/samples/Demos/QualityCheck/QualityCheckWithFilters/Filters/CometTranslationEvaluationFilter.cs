// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using QualityCheckWithFilters.Models;
using QualityCheckWithFilters.Services;

namespace QualityCheckWithFilters.Filters;

internal sealed class CometTranslationEvaluationFilter(
    EvaluationService evaluationService,
    ILogger logger,
    double threshold) : IFunctionInvocationFilter
{
    public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        await next(context);

        var sourceText = context.Result.RenderedPrompt!;
        var translation = context.Result.ToString();

        logger.LogInformation("Translation: {Translation}", translation);

        var request = new TranslationEvaluationRequest { Sources = [sourceText], Translations = [translation] };
        var response = await evaluationService.EvaluateAsync<TranslationEvaluationRequest, CometTranslationEvaluationResponse>(request);

        var score = Math.Round(response.Scores[0], 4);

        logger.LogInformation("[COMET] Score: {Score}", score);

        if (score < threshold)
        {
            throw new KernelException($"COMET translation evaluation score ({score}) is lower than threshold ({threshold})");
        }
    }
}
