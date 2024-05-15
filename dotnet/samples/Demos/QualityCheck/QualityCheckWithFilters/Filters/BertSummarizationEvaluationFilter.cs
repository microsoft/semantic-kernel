// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using QualityCheckWithFilters.Models;
using QualityCheckWithFilters.Services;

namespace QualityCheckWithFilters.Filters;

internal sealed class BertSummarizationEvaluationFilter(
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
        var response = await evaluationService.EvaluateAsync<SummarizationEvaluationRequest, BertSummarizationEvaluationResponse>(request);

        var precision = Math.Round(response.Precision[0], 4);
        var recall = Math.Round(response.Recall[0], 4);
        var f1 = Math.Round(response.F1[0], 4);

        logger.LogInformation("[BERT] Precision: {Precision}, Recall: {Recall}, F1: {F1}", precision, recall, f1);

        if (f1 < threshold)
        {
            throw new KernelException($"BERT summary evaluation score ({f1}) is lower than threshold ({threshold})");
        }
    }
}
