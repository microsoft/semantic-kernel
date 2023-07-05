// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using System.Threading.Tasks;
using RepoUtils;

public static class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main()
    {
        // Load configuration
        IConfigurationRoot config = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<Env>()
            .Build();

        Example01_NativeFunctions.Run(config);
        Console.WriteLine("== DONE ==");

        await Example02_Pipeline.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example03_Variables.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example04_CombineLLMPromptsAndNativeCode.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example05_InlineFunctionDefinition.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example06_TemplateLanguage.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example07_BingAndGoogleSkills.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example08_RetryHandler.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example09_FunctionTypes.RunAsync(config);
        Console.WriteLine("== DONE ==");

        Example10_DescribeAllSkillsAndFunctions.Run(config);
        Console.WriteLine("== DONE ==");

        await Example11_WebSearchQueries.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example12_SequentialPlanner.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example13_ConversationSummarySkill.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example14_SemanticMemory.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example15_MemorySkill.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example16_CustomLLM.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example17_ChatGPT.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example18_DallE.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example19_Qdrant.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example20_HuggingFace.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example21_ChatGptPlugins.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example22_OpenApiSkill_AzureKeyVault.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example23_OpenApiSkill_GitHub.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example24_OpenApiSkill_Jira.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example25_ReadOnlyMemoryStore.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example26_AADAuth.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example27_SemanticFunctionsUsingChatGPT.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example28_ActionPlanner.RunAsync(config);
        Console.WriteLine("== DONE ==");

        Example29_Tokenizer.Run(config);
        Console.WriteLine("== DONE ==");

        await Example30_ChatWithPrompts.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example31_CustomPlanner.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example32_StreamingCompletion.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example33_StreamingChat.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example34_CustomChatModel.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example35_GrpcSkills.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example36_MultiCompletion.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example37_MultiStreamingCompletion.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example38_Pinecone.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example39_Postgres.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example40_DIContainer.RunAsync(config);
        Console.WriteLine("== DONE ==");

        Example41_HttpClientUsage.Run(config);
        Console.WriteLine("== DONE ==");

        Example42_KernelBuilder.Run(config);
        Console.WriteLine("== DONE ==");

        await Example43_GetModelResult.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example44_MultiChatCompletion.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example45_MultiStreamingChatCompletion.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example46_Weaviate.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example47_Redis.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example48_GroundednessChecks.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example49_LogitBias.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example50_Chroma.RunAsync(config);
        Console.WriteLine("== DONE ==");

        await Example51_StepwisePlanner.RunAsync(config);
        Console.WriteLine("== DONE ==");
    }
}
