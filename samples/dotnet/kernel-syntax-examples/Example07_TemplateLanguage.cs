// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.CoreSkills;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example07_TemplateLanguage
{
    /// <summary>
    /// Show how to invoke a Native Function written in C#
    /// from a Semantic Function written in natural language
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== TemplateLanguage ========");

        IKernel kernel = Kernel.Builder.WithLogger(ConsoleLogger.Log).Build();
        kernel.Config.AddOpenAITextCompletionService("text-davinci-003", "text-davinci-003", Env.Var("OPENAI_API_KEY"));

        // Load native skill into the kernel skill collection, sharing its functions with prompt templates
        // Functions loaded here are available as "time.*"
        kernel.ImportSkill(new TimeSkill(), "time");

        // Semantic Function invoking time.Date and time.Time native functions
        const string FUNCTION_DEFINITION = @"
Today is: {{time.Date}}
Current time is: {{time.Time}}

Answer to the following questions using JSON syntax, including the data used.
Is it morning, afternoon, evening, or night (morning/afternoon/evening/night)?
Is it weekend time (weekend/not weekend)?
";
        var kindOfDay = kernel.CreateSemanticFunction(FUNCTION_DEFINITION, maxTokens: 150);

        var result = await kindOfDay.InvokeAsync();
        Console.WriteLine(result);
    }
}
