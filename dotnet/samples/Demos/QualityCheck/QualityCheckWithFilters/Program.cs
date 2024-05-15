// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using QualityCheckWithFilters.Filters;
using QualityCheckWithFilters.Models;
using QualityCheckWithFilters.Services;

namespace QualityCheckWithFilters;

public class Program
{
    public static async Task Main()
    {
        await SummarizationEvaluationAsync(EvaluationScoreType.BERT, threshold: 0.85);

        // Output:
        // Extractive summary: [BERT] Precision: 0.9756, Recall: 0.9114, F1: 0.9424
        // Abstractive summary: [BERT] Precision: 0.8953, Recall: 0.8656, F1: 0.8802
        // Random summary: [BERT] Precision: 0.8433, Recall: 0.787, F1: 0.8142
        // Exception occurred during function invocation: BERT summary evaluation score (0.8142) is lower than threshold (0.85)

        await SummarizationEvaluationAsync(EvaluationScoreType.BLEU, threshold: 0.5);

        // Output:
        // Extractive summary: [BLEU] Score: 0.3281, Precisions: 1, 1, 0.9726, 0.9444, Brevity penalty: 0.3351, Length Ratio: 0.4777
        // Abstractive summary: [BLEU] Score: 0, Precisions: 0.678, 0.1552, 0.0175, 0, Brevity penalty: 0.1899, Length Ratio: 0.3758
        // Random summary: [BLEU] Score: 0, Precisions: 0.2, 0, 0, 0, Brevity penalty: 0, Length Ratio: 0.0318
        // Exception occurred during function invocation: BLEU summary evaluation score (0.2) is lower than threshold (0.5)

        await SummarizationEvaluationAsync(EvaluationScoreType.METEOR, threshold: 0.1);

        // Output:
        // Extractive summary: [METEOR] Score: 0.438
        // Abstractive summary: [METEOR] Score: 0.1661
        // Random summary: [METEOR] Score: 0.0035
        // Exception occurred during function invocation: METEOR summary evaluation score (0.0035) is lower than threshold (0.1)
    }

    #region Scenarios

    private static async Task SummarizationEvaluationAsync(EvaluationScoreType scoreType, double threshold)
    {
        const string TextToSummarize =
            """
            The sun rose over the horizon, casting a warm glow across the landscape.
            Birds began to chirp, greeting the new day with their melodious songs.
            The flowers in the garden slowly opened their petals, revealing vibrant colors and delicate fragrances.
            A gentle breeze rustled through the trees, creating a soothing sound that complemented the morning stillness.
            People started to emerge from their homes, ready to embark on their daily routines.
            Some went for a morning jog, enjoying the fresh air and the peaceful surroundings.
            Others sipped their coffee while reading the newspaper on their porches.
            The streets gradually filled with the hum of cars and the chatter of pedestrians.
            In the park, children played joyfully, their laughter echoing through the air.
            As the day progressed, the town buzzed with activity, each moment bringing new opportunities and experiences.
            """;

        const string ExtractiveSummary =
            """
            The sun rose over the horizon, casting a warm glow across the landscape.
            Birds began to chirp, greeting the new day with their melodious songs.
            People started to emerge from their homes, ready to embark on their daily routines.
            The streets gradually filled with the hum of cars and the chatter of pedestrians.
            In the park, children played joyfully, their laughter echoing through the air.
            """;

        const string AbstractiveSummary =
            """
            As the sun rises, nature awakens with birds singing and flowers blooming.
            People begin their day with various routines, from jogging to enjoying coffee.
            The town gradually becomes lively with the sounds of traffic and children's laughter in the park,
            marking the start of a bustling day filled with new activities and opportunities.
            """;

        const string RandomSummary =
            """
            This is random text.
            """;

        var builder = Kernel.CreateBuilder();

        builder.Services.AddLogging(loggingBuilder => loggingBuilder.AddConsole().SetMinimumLevel(LogLevel.Information));

        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("extractive-summary-model", ExtractiveSummary));
        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("abstractive-summary-model", AbstractiveSummary));
        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("random-summary-model", RandomSummary));

        builder.Services.AddHttpClient("default", client => { client.BaseAddress = new Uri("http://localhost:8080"); });

        builder.Services.AddSingleton<EvaluationService>(
            sp => new EvaluationService(
                sp.GetRequiredService<IHttpClientFactory>().CreateClient("default"),
                scoreType.Endpoint));

        builder.Services.AddSingleton<IFunctionInvocationFilter>(
            sp => FilterFactory.Create(
                scoreType,
                sp.GetRequiredService<EvaluationService>(),
                sp.GetRequiredService<ILogger<Program>>(),
                threshold));

        var kernel = builder.Build();

        await InvokeAsync(kernel, TextToSummarize, "extractive-summary-model");
        await InvokeAsync(kernel, TextToSummarize, "abstractive-summary-model");
        await InvokeAsync(kernel, TextToSummarize, "random-summary-model");
    }

    #endregion

    #region Helpers

    private static async Task InvokeAsync(Kernel kernel, string input, string modelId)
    {
        var logger = kernel.Services.GetRequiredService<ILogger<Program>>();

        try
        {
            await kernel.InvokePromptAsync(input, new(new PromptExecutionSettings { ModelId = modelId }));
        }
        catch (KernelException exception)
        {
            logger.LogError(exception, "Exception occurred during function invocation: {Message}", exception.Message);
        }
    }

    #endregion
}
