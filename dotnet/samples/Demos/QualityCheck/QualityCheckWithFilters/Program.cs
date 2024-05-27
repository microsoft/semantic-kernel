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
    /// <summary>
    /// This example demonstrates how to evaluate LLM results on tasks such as text summarization and translation
    /// using following metrics:
    /// - BERTScore: https://github.com/Tiiiger/bert_score
    /// - BLEU (BiLingual Evaluation Understudy): https://en.wikipedia.org/wiki/BLEU
    /// - METEOR (Metric for Evaluation of Translation with Explicit ORdering): https://en.wikipedia.org/wiki/METEOR
    /// - COMET (Crosslingual Optimized Metric for Evaluation of Translation): https://unbabel.github.io/COMET
    /// Semantic Kernel Filters are used to perform following tasks during function invocation:
    /// 1. Get original text to summarize/translate.
    /// 2. Get LLM result.
    /// 3. Call evaluation server to get specific metric score.
    /// 4. Compare metric score to configured threshold and throw an exception if score is lower.
    /// </summary>
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

        await TranslationEvaluationAsync(threshold: 0.4);

        // Output:
        // Text to translate: Berlin ist die Hauptstadt der Deutschland.
        // Translation: Berlin is the capital of Germany - [COMET] Score: 0.8695
        // Translation: Berlin capital Germany is of The - [COMET] Score: 0.4724
        // Translation: This is random translation - [COMET] Score: 0.3525
        // Exception occurred during function invocation: COMET translation evaluation score (0.3525) is lower than threshold (0.4)
    }

    #region Scenarios

    /// <summary>
    /// This method performs summarization evaluation and compare following types of summaries:
    /// - Extractive summary: involves selecting and extracting key sentences, phrases, or segments directly from the original text to create a summary.
    /// - Abstractive summary: involves generating new sentences that convey the key information from the original text.
    /// - Random summary: unrelated text to original source for comparison purposes.
    /// </summary>
    private static async Task SummarizationEvaluationAsync(EvaluationScoreType scoreType, double threshold)
    {
        // Define text to summarize and possible LLM summaries.
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

        // Get kernel builder with initial configuration.
        var builder = GetKernelBuilder(scoreType, threshold);

        // It doesn't matter which LLM to use for text summarization, since the main goal is to demonstrate how to evaluate the result and compare metrics.
        // For demonstration purposes, fake chat completion service is used to simulate LLM response with predefined summary.
        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("extractive-summary-model", ExtractiveSummary));
        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("abstractive-summary-model", AbstractiveSummary));
        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("random-summary-model", RandomSummary));

        // Build kernel
        var kernel = builder.Build();

        // Invoke function to perform text summarization with predefined result, trigger function invocation filter and evaluate the result.
        await InvokeAsync(kernel, TextToSummarize, "extractive-summary-model");
        await InvokeAsync(kernel, TextToSummarize, "abstractive-summary-model");
        await InvokeAsync(kernel, TextToSummarize, "random-summary-model");
    }

    /// <summary>
    /// This method performs translation evaluation and compare the results.
    /// </summary>
    private static async Task TranslationEvaluationAsync(double threshold)
    {
        EvaluationScoreType scoreType = EvaluationScoreType.COMET;

        // Define text to translate and possible LLM translations.
        const string TextToTranslate = "Berlin ist die Hauptstadt der Deutschland.";
        const string Translation1 = "Berlin is the capital of Germany.";
        const string Translation2 = "Berlin capital Germany is of The.";
        const string Translation3 = "This is random translation.";

        // Get kernel builder with initial configuration.
        var builder = GetKernelBuilder(scoreType, threshold);

        // It doesn't matter which LLM to use for text translation, since the main goal is to demonstrate how to evaluate the result and compare metrics.
        // For demonstration purposes, fake chat completion service is used to simulate LLM response with predefined translation.
        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("translation-1-model", Translation1));
        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("translation-2-model", Translation2));
        builder.Services.AddSingleton<IChatCompletionService>(new FakeChatCompletionService("translation-3-model", Translation3));

        // Build kernel
        var kernel = builder.Build();

        // Invoke function to perform text translation with predefined result, trigger function invocation filter and evaluate the result.
        await InvokeAsync(kernel, TextToTranslate, "translation-1-model");
        await InvokeAsync(kernel, TextToTranslate, "translation-2-model");
        await InvokeAsync(kernel, TextToTranslate, "translation-3-model");
    }

    #endregion

    #region Helpers

    /// <summary>
    /// Gets kernel builder with initial configuration.
    /// </summary>
    private static IKernelBuilder GetKernelBuilder(EvaluationScoreType scoreType, double threshold)
    {
        // Create kernel builder
        var builder = Kernel.CreateBuilder();

        // Add logging
        builder.Services.AddLogging(loggingBuilder => loggingBuilder.AddConsole().SetMinimumLevel(LogLevel.Information));

        // Add default HTTP client with base address to local evaluation server
        builder.Services.AddHttpClient("default", client => { client.BaseAddress = new Uri("http://localhost:8080"); });

        // Add service which performs HTTP requests to evaluation server
        builder.Services.AddSingleton<EvaluationService>(
            sp => new EvaluationService(
                sp.GetRequiredService<IHttpClientFactory>().CreateClient("default"),
                scoreType.Endpoint));

        // Add function invocation filter to perform evaluation and compare metric score with configured threshold
        builder.Services.AddSingleton<IFunctionInvocationFilter>(
            sp => FilterFactory.Create(
                scoreType,
                sp.GetRequiredService<EvaluationService>(),
                sp.GetRequiredService<ILogger<Program>>(),
                threshold));

        return builder;
    }

    /// <summary>
    /// Invokes kernel function with provided input and model ID.
    /// </summary>
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
