// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Reliability;
using RepoUtils;

public static class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main(string[] args)
    {
        // Load configuration from environment variables or user secrets.
        LoadUserSecrets();

        // Execution canceled if the user presses Ctrl+C.
        using CancellationTokenSource cancellationTokenSource = new();
        CancellationToken cancelToken = cancellationTokenSource.ConsoleCancellationToken();

        // Check if args[0] is provided
        string? filter = args.Length > 0 ? args[0] : null;

        // Run examples based on the filter
        await RunExamplesAsync(filter, cancelToken);
    }

    private static async Task RunExamplesAsync(string? filter, CancellationToken cancellationToken)
    {
        // List of all available examples
        var examples = new Dictionary<string, Func<CancellationToken, Task>>
        {
            { nameof(Example01_NativeFunctions), async (_) => {await Example01_NativeFunctions.RunAsync(); }},
            { nameof(Example02_Pipeline), async (_) => {await Example02_Pipeline.RunAsync(); } },
            { nameof(Example03_Variables), async (_) => {await Example03_Variables.RunAsync(); }},
            { nameof(Example04_CombineLLMPromptsAndNativeCode), async (_) => {await Example04_CombineLLMPromptsAndNativeCode.RunAsync(); }},
            { nameof(Example05_InlineFunctionDefinition), async (_) => {await Example05_InlineFunctionDefinition.RunAsync(); }},
            { nameof(Example06_TemplateLanguage), async (_) => {await Example06_TemplateLanguage.RunAsync(); }},
            { nameof(Example07_BingAndGoogleSkills), async (_) => {await Example07_BingAndGoogleSkills.RunAsync(); }},
            { nameof(Example08_RetryHandler), async (_) => {await Example08_RetryHandler.RunAsync(); }},
            { nameof(Example09_FunctionTypes), async (_) => {await Example09_FunctionTypes.RunAsync(); }},
            { nameof(Example10_DescribeAllSkillsAndFunctions), async (_) => {await Example10_DescribeAllSkillsAndFunctions.RunAsync(); }},
            { nameof(Example11_WebSearchQueries), async (_) => {await Example11_WebSearchQueries.RunAsync(); }},
            { nameof(Example12_SequentialPlanner), async (_) => {await Example12_SequentialPlanner.RunAsync(); }},
            { nameof(Example13_ConversationSummarySkill), async (_) => {await Example13_ConversationSummarySkill.RunAsync(); }},
            { nameof(Example14_SemanticMemory), async (_) => {await Example14_SemanticMemory.RunAsync(); }},
            { nameof(Example15_TextMemorySkill), async (ct) => {await Example15_TextMemorySkill.RunAsync(ct); } },
            { nameof(Example16_CustomLLM), async (_) => {await Example16_CustomLLM.RunAsync(); }},
            { nameof(Example17_ChatGPT), async (_) => {await Example17_ChatGPT.RunAsync(); }},
            { nameof(Example18_DallE), async (_) => {await Example18_DallE.RunAsync(); }},
            { nameof(Example20_HuggingFace), async (_) => {await Example20_HuggingFace.RunAsync(); }},
            { nameof(Example21_ChatGptPlugins), async (_) => {await Example21_ChatGptPlugins.RunAsync(); }},
            { nameof(Example22_OpenApiSkill_AzureKeyVault), async (_) => {await Example22_OpenApiSkill_AzureKeyVault.RunAsync(); }},
            { nameof(Example23_OpenApiSkill_GitHub), async (_) => {await Example23_OpenApiSkill_GitHub.RunAsync(); }},
            { nameof(Example24_OpenApiSkill_Jira), async (_) => {await Example24_OpenApiSkill_Jira.RunAsync(); }},
            { nameof(Example25_ReadOnlyMemoryStore), async (_) => {await Example25_ReadOnlyMemoryStore.RunAsync(); }},
            { nameof(Example26_AADAuth), async (_) => {await Example26_AADAuth.RunAsync(); }},
            { nameof(Example27_SemanticFunctionsUsingChatGPT), async (_) => {await Example27_SemanticFunctionsUsingChatGPT.RunAsync(); }},
            { nameof(Example28_ActionPlanner), async (_) => {await Example28_ActionPlanner.RunAsync(); }},
            { nameof(Example29_Tokenizer), async (_) => {await Example29_Tokenizer.RunAsync(); }},
            { nameof(Example30_ChatWithPrompts), async (_) => {await Example30_ChatWithPrompts.RunAsync(); }},
            { nameof(Example31_CustomPlanner), async (_) => {await Example31_CustomPlanner.RunAsync(); }},
            { nameof(Example32_StreamingCompletion), async (_) => {await Example32_StreamingCompletion.RunAsync(); }},
            { nameof(Example33_StreamingChat), async (_) => {await Example33_StreamingChat.RunAsync(); }},
            { nameof(Example34_CustomChatModel), async (_) => {await Example34_CustomChatModel.RunAsync(); }},
            { nameof(Example35_GrpcSkills), async (_) => {await Example35_GrpcSkills.RunAsync(); }},
            { nameof(Example36_MultiCompletion), async (_) => {await Example36_MultiCompletion.RunAsync(); }},
            { nameof(Example37_MultiStreamingCompletion), async (_) => {await Example37_MultiStreamingCompletion.RunAsync(); }},
            { nameof(Example40_DIContainer), async (_) => {await Example40_DIContainer.RunAsync(); }},
            { nameof(Example41_HttpClientUsage), async (_) => {await Example41_HttpClientUsage.RunAsync(); }},
            { nameof(Example42_KernelBuilder), async (_) => {await Example42_KernelBuilder.RunAsync(); }},
            { nameof(Example43_GetModelResult), async (_) => {await Example43_GetModelResult.RunAsync(); }},
            { nameof(Example44_MultiChatCompletion), async (_) => {await Example44_MultiChatCompletion.RunAsync(); }},
            { nameof(Example45_MultiStreamingChatCompletion), async (_) => {await Example45_MultiStreamingChatCompletion.RunAsync(); }},
            { nameof(Example48_GroundednessChecks), async (_) => {await Example48_GroundednessChecks.RunAsync(); }},
            { nameof(Example49_LogitBias), async (_) => {await Example49_LogitBias.RunAsync(); }},
            { nameof(Example51_StepwisePlanner), async (_) => {await Example51_StepwisePlanner.RunAsync(); }},
            { nameof(Example52_ApimAuth), async (_) => {await Example52_ApimAuth.RunAsync(); }},
            { nameof(Example54_AzureChatCompletionWithData), async (_) => {await Example54_AzureChatCompletionWithData.RunAsync(); }},
            { nameof(Example55_TextChunker), async (_) => {await Example55_TextChunker.RunAsync(); }},
            { nameof(Example56_TemplateNativeFunctionsWithMultipleArguments), async (_) => {await Example56_TemplateNativeFunctionsWithMultipleArguments.RunAsync(); }},
        };

        // Filter and run examples
        foreach (var example in examples)
        {
            if (string.IsNullOrEmpty(filter) || example.Key.Contains(filter, StringComparison.OrdinalIgnoreCase))
            {
                try
                {
                    Console.WriteLine($"Running {example.Key}...");
                    await example.Value(cancellationToken).SafeWaitAsync(cancellationToken);
                }
                catch (ConfigurationNotFoundException ex)
                {
                    Console.WriteLine($"{ex.Message}. Skipping example {example.Key}.");
                }
            }
        }
    }

    private static void LoadUserSecrets()
    {
        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .AddUserSecrets<Env>()
            .Build();
        TestConfiguration.Initialize(configRoot);
    }

    private static CancellationToken ConsoleCancellationToken(this CancellationTokenSource tokenSource)
    {
        Console.CancelKeyPress += (s, e) =>
        {
            Console.WriteLine("Canceling...");
            tokenSource.Cancel();
            e.Cancel = true;
        };

        return tokenSource.Token;
    }

    private static async Task SafeWaitAsync(this Task task,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await task.WaitAsync(cancellationToken);
            Console.WriteLine("== DONE ==");
        }
        catch (ConfigurationNotFoundException ex)
        {
            Console.WriteLine($"{ex.Message}. Skipping example.");
        }

        cancellationToken.ThrowIfCancellationRequested();
    }
}
