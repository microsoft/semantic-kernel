// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using QualityCheckWithFilters.Models;
using QualityCheckWithFilters.Services;

namespace QualityCheckWithFilters.Filters;

/// <summary>
/// Filter which performs text summarization evaluation using METEOR metric: https://huggingface.co/spaces/evaluate-metric/meteor.
/// METEOR score ranges from 0 to 1, where higher values indicate better similarity between original text and generated summary.
/// </summary>
internal sealed class MeteorSummarizationEvaluationFilter(
    EvaluationService evaluationService,
    ILogger logger,
    double threshold) : IFunctionInvocationFilter
{
    public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        await next(context);

        var sourceText = context.Result.RenderedPrompt!;
        var summary = context.Result.ToString();

        var request = new SummarizationEvaluationRequest { Sources = [sourceText], Summaries = [summary] };
        var response = await evaluationService.EvaluateAsync<SummarizationEvaluationRequest, MeteorSummarizationEvaluationResponse>(request);

        var score = Math.Round(response.Score, 4);

        logger.LogInformation("[METEOR] Score: {Score}", score);

        if (score < threshold)
        {
            throw new KernelException($"METEOR summary evaluation score ({score}) is lower than threshold ({threshold})");
        }
    }
}
