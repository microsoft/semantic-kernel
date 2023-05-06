// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;

#pragma warning disable CS1591
public static class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main()
    {
        //Debug.WriteLine($"before: {Environment.GetEnvironmentVariable("AAA")}");
        //Debug.WriteLine($"before: {Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY")}");
        //Debug.WriteLine($"before: {Environment.GetEnvironmentVariable("AZURE_OPENAI_KEY")}");
        //Debug.WriteLine($"before: {Environment.GetEnvironmentVariable("AZUURE_OPENAI_KEY")}");
        //Environment.SetEnvironmentVariable("AZURE_OPENAI_KEY", "a");
        //Debug.WriteLine(Environment.GetEnvironmentVariable("AZURE_OPENAI_KEY"));

        await Example12_Planning.RunAsync();
        Console.WriteLine("== DONE ==");

        Example01_NativeFunctions.Run();
        Console.WriteLine("== DONE ==");

        await Example02_Pipeline.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example03_Variables.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example04_BingSkillAndConnector.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example05_CombineLLMPromptsAndNativeCode.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example06_InlineFunctionDefinition.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example07_TemplateLanguage.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example08_RetryMechanism.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example09_FunctionTypes.RunAsync();
        Console.WriteLine("== DONE ==");

        Example10_DescribeAllSkillsAndFunctions.Run();
        Console.WriteLine("== DONE ==");

        await Example11_WebSearchQueries.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example12_Planning.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example13_ConversationSummarySkill.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example14_Memory.RunAsync();
        Console.WriteLine("== DONE ==");

        await Example15_MemorySkill.RunAsync();
        Console.WriteLine("== DONE ==");
    }
}
#pragma warning restore CS1591
