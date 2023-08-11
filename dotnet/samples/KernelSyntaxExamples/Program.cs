// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Reliability;
using RepoUtils;

public static class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main()
    {
        // Load configuration from environment variables or user secrets.
        LoadUserSecrets();

        // Execution canceled if the user presses Ctrl+C.
        using CancellationTokenSource cancellationTokenSource = new();
        CancellationToken cancelToken = cancellationTokenSource.ConsoleCancellationToken();

        // Run examples
        await Example01_NativeFunctions.RunAsync().SafeWaitAsync(cancelToken);
        await Example02_Pipeline.RunAsync().SafeWaitAsync(cancelToken);
        await Example03_Variables.RunAsync().SafeWaitAsync(cancelToken);
        await Example04_CombineLLMPromptsAndNativeCode.RunAsync().SafeWaitAsync(cancelToken);
        await Example05_InlineFunctionDefinition.RunAsync().SafeWaitAsync(cancelToken);
        await Example06_TemplateLanguage.RunAsync().SafeWaitAsync(cancelToken);
        await Example07_BingAndGoogleSkills.RunAsync().SafeWaitAsync(cancelToken);
        await Example08_RetryHandler.RunAsync().SafeWaitAsync(cancelToken);
        await Example09_FunctionTypes.RunAsync().SafeWaitAsync(cancelToken);
        await Example10_DescribeAllSkillsAndFunctions.RunAsync().SafeWaitAsync(cancelToken);
        await Example11_WebSearchQueries.RunAsync().SafeWaitAsync(cancelToken);
        await Example12_SequentialPlanner.RunAsync().SafeWaitAsync(cancelToken);
        await Example13_ConversationSummarySkill.RunAsync().SafeWaitAsync(cancelToken);
        await Example14_SemanticMemory.RunAsync().SafeWaitAsync(cancelToken);
        await Example15_MemorySkill.RunAsync().SafeWaitAsync(cancelToken);
        await Example16_CustomLLM.RunAsync().SafeWaitAsync(cancelToken);
        await Example17_ChatGPT.RunAsync().SafeWaitAsync(cancelToken);
        await Example18_DallE.RunAsync().SafeWaitAsync(cancelToken);
        await Example19_Qdrant.RunAsync().SafeWaitAsync(cancelToken);
        await Example20_HuggingFace.RunAsync().SafeWaitAsync(cancelToken);
        await Example21_ChatGptPlugins.RunAsync().SafeWaitAsync(cancelToken);
        await Example22_OpenApiSkill_AzureKeyVault.RunAsync().SafeWaitAsync(cancelToken);
        await Example23_OpenApiSkill_GitHub.RunAsync().SafeWaitAsync(cancelToken);
        await Example24_OpenApiSkill_Jira.RunAsync().SafeWaitAsync(cancelToken);
        await Example25_ReadOnlyMemoryStore.RunAsync().SafeWaitAsync(cancelToken);
        await Example26_AADAuth.RunAsync().SafeWaitAsync(cancelToken);
        await Example27_SemanticFunctionsUsingChatGPT.RunAsync().SafeWaitAsync(cancelToken);
        await Example28_ActionPlanner.RunAsync().SafeWaitAsync(cancelToken);
        await Example29_Tokenizer.RunAsync().SafeWaitAsync(cancelToken);
        await Example30_ChatWithPrompts.RunAsync().SafeWaitAsync(cancelToken);
        await Example31_CustomPlanner.RunAsync().SafeWaitAsync(cancelToken);
        await Example32_StreamingCompletion.RunAsync().SafeWaitAsync(cancelToken);
        await Example33_StreamingChat.RunAsync().SafeWaitAsync(cancelToken);
        await Example34_CustomChatModel.RunAsync().SafeWaitAsync(cancelToken);
        await Example35_GrpcSkills.RunAsync().SafeWaitAsync(cancelToken);
        await Example36_MultiCompletion.RunAsync().SafeWaitAsync(cancelToken);
        await Example37_MultiStreamingCompletion.RunAsync().SafeWaitAsync(cancelToken);
        await Example38_Pinecone.RunAsync().SafeWaitAsync(cancelToken);
        await Example39_Postgres.RunAsync().SafeWaitAsync(cancelToken);
        await Example40_DIContainer.RunAsync().SafeWaitAsync(cancelToken);
        await Example41_HttpClientUsage.RunAsync().SafeWaitAsync(cancelToken);
        await Example42_KernelBuilder.RunAsync().SafeWaitAsync(cancelToken);
        await Example43_GetModelResult.RunAsync().SafeWaitAsync(cancelToken);
        await Example44_MultiChatCompletion.RunAsync().SafeWaitAsync(cancelToken);
        await Example45_MultiStreamingChatCompletion.RunAsync().SafeWaitAsync(cancelToken);
        await Example46_Weaviate.RunAsync().SafeWaitAsync(cancelToken);
        await Example47_Redis.RunAsync().SafeWaitAsync(cancelToken);
        await Example48_GroundednessChecks.RunAsync().SafeWaitAsync(cancelToken);
        await Example49_LogitBias.RunAsync().SafeWaitAsync(cancelToken);
        await Example50_Chroma.RunAsync().SafeWaitAsync(cancelToken);
        await Example51_StepwisePlanner.RunAsync().SafeWaitAsync(cancelToken);
        await Example52_ApimAuth.RunAsync().SafeWaitAsync(cancelToken);
        await Example53_Kusto.RunAsync().SafeWaitAsync(cancelToken);
        await Example54_FunctionHooks.RunAsync().SafeWaitAsync(cancelToken);
        await Example55_PlanHooks.RunAsync().SafeWaitAsync(cancelToken);
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
