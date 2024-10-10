// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using QualityCheckWithFilters.Models;
using QualityCheckWithFilters.Services;

namespace QualityCheckWithFilters.Filters;

/// <summary>
/// Factory class for function invocation filters based on evaluation score type.
/// </summary>
internal sealed class FilterFactory
{
    private static readonly Dictionary<EvaluationScoreType, Func<EvaluationService, ILogger, double, IFunctionInvocationFilter>> s_filters = new()
    {
        [EvaluationScoreType.BERT] = (service, logger, threshold) => new BertSummarizationEvaluationFilter(service, logger, threshold),
        [EvaluationScoreType.BLEU] = (service, logger, threshold) => new BleuSummarizationEvaluationFilter(service, logger, threshold),
        [EvaluationScoreType.METEOR] = (service, logger, threshold) => new MeteorSummarizationEvaluationFilter(service, logger, threshold),
        [EvaluationScoreType.COMET] = (service, logger, threshold) => new CometTranslationEvaluationFilter(service, logger, threshold),
    };

    public static IFunctionInvocationFilter Create(EvaluationScoreType type, EvaluationService evaluationService, ILogger logger, double threshold)
        => s_filters[type].Invoke(evaluationService, logger, threshold);
}
