// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using QualityCheckWithFilters.Models;
using QualityCheckWithFilters.Services;

namespace QualityCheckWithFilters.Filters;

/// <summary>
/// Filter which performs text summarization evaluation using BLEU metric: https://huggingface.co/spaces/evaluate-metric/bleu.
/// Evaluation result contains values like score, precisions, brevity penalty and length ratio.
/// The closer the score and precision values are to 1 - the better the quality of the summary.
/// </summary>
internal sealed class BleuSummarizationEvaluationFilter(
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
        var response = await evaluationService.EvaluateAsync<SummarizationEvaluationRequest, BleuSummarizationEvaluationResponse>(request);

        var score = Math.Round(response.Score, 4);
        var precisions = response.Precisions.Select(l => Math.Round(l, 4)).ToList();
        var brevityPenalty = Math.Round(response.BrevityPenalty, 4);
        var lengthRatio = Math.Round(response.LengthRatio, 4);

        logger.LogInformation("[BLEU] Score: {Score}, Precisions: {Precisions}, Brevity penalty: {BrevityPenalty}, Length Ratio: {LengthRatio}",
            score,
            string.Join(", ", precisions),
            brevityPenalty,
            lengthRatio);

        if (precisions[0] < threshold)
        {
            throw new KernelException($"BLEU summary evaluation score ({precisions[0]}) is lower than threshold ({threshold})");
        }
    }
}
