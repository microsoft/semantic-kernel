// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

public static class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main()
    {
        Example01_NativeFunctions.Run();
        Console.WriteLine("== DONE ==");

        await Example02_Pipeline.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example03_Variables.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example04_CombineLLMPromptsAndNativeCode.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example05_InlineFunctionDefinition.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example06_TemplateLanguage.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example07_BingAndGoogleSkills.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example08_RetryHandler.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example09_FunctionTypes.RunAsync();
        Console.WriteLine("== DONE ==");

        Example10_DescribeAllSkillsAndFunctions.Run();
        Console.WriteLine("== DONE ==");

        await Example11_WebSearchQueries.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example12_SequentialPlanner.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example13_ConversationSummarySkill.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example14_SemanticMemory.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example15_MemorySkill.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example16_CustomLLM.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example17_ChatGPT.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example18_DallE.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example19_Qdrant.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example20_HuggingFace.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example21_ChatGptPlugins.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example22_OpenApiSkill_AzureKeyVault.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example23_OpenApiSkill_GitHub.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example24_OpenApiSkill_Jira.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example25_ReadOnlyMemoryStore.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example26_AADAuth.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example27_SemanticFunctionsUsingChatGPT.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example28_ActionPlanner.RunAsync();
        Console.WriteLine("== DONE ==");

        Example29_Tokenizer.Run();
        Console.WriteLine("== DONE ==");

        await Example30_ChatWithPrompts.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example31_CustomPlanner.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example32_StreamingCompletion.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example33_StreamingChat.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example34_CustomChatModel.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example35_GrpcSkills.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example36_MultiCompletion.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example37_MultiStreamingCompletion.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example38_Pinecone.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example39_Postgres.RunAsync();

        await Example40_DIContainer.RunAsync();
        Console.WriteLine("== DONE ==");

        Example41_HttpClientUsage.Run();
        Console.WriteLine("== DONE ==");

        Example42_KernelBuilder.Run();
        Console.WriteLine("== DONE ==");

        await Example43_GetModelResult.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example44_MultiChatCompletion.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example45_MultiStreamingChatCompletion.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example46_Weaviate.RunAsync();
        Console.WriteLine("== DONE ==");
    }
}
