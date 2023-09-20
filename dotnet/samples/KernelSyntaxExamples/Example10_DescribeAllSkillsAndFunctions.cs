// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;
using Skills;

// ReSharper disable once InconsistentNaming
public static class Example10_DescribeAllSkillsAndFunctions
{
    /// <summary>
    /// Print a list of all the functions imported into the kernel, including function descriptions,
    /// list of parameters, parameters descriptions, etc.
    /// See the end of the file for a sample of what the output looks like.
    /// </summary>
    public static Task RunAsync()
    {
        Console.WriteLine("======== Describe all skills and functions ========");

        var kernel = Kernel.Builder
            .WithOpenAIChatCompletionService(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Import a native skill
        var skill1 = new StaticTextPlugin();
        kernel.ImportSkill(skill1, "StaticTextskill");

        // Import another native skill
        var skill2 = new TextPlugin();
        kernel.ImportSkill(skill2, "AnotherTextskill");

        // Import a semantic skill
        string folder = RepoFiles.SampleSkillsPath();
        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill");

        // Define a semantic function inline, without naming
        var sFun1 = kernel.CreateSemanticFunction("tell a joke about {{$input}}", requestSettings: new OpenAIRequestSettings() { MaxTokens = 150 });

        // Define a semantic function inline, with skill name
        var sFun2 = kernel.CreateSemanticFunction(
            "write a novel about {{$input}} in {{$language}} language",
            skillName: "Writing",
            functionName: "Novel",
            description: "Write a bedtime story",
            requestSettings: new OpenAIRequestSettings() { MaxTokens = 150 });

        var functions = kernel.Skills.GetFunctionViews();

        Console.WriteLine("*****************************************");
        Console.WriteLine("****** Registered skills and functions ******");
        Console.WriteLine("*****************************************");
        Console.WriteLine();

        foreach (FunctionView func in functions)
        {
            PrintFunction(func);
        }

        return Task.CompletedTask;
    }

    private static void PrintFunction(FunctionView func)
    {
        Console.WriteLine($"   {func.Name}: {func.Description}");

        if (func.Parameters.Count > 0)
        {
            Console.WriteLine("      Params:");
            foreach (var p in func.Parameters)
            {
                Console.WriteLine($"      - {p.Name}: {p.Description}");
                Console.WriteLine($"        default: '{p.DefaultValue}'");
            }
        }

        Console.WriteLine();
    }
}

#pragma warning disable CS1587 // XML comment is not placed on a valid language element
/** Sample output:

*****************************************
****** Native skills and functions ******
*****************************************

Skill: StaticTextskill
   Uppercase: Change all string chars to uppercase
      Params:
      - input: Text to uppercase
        default: ''

   AppendDay: Append the day variable
      Params:
      - input: Text to append to
        default: ''
      - day: Value of the day to append
        default: ''

Skill: Textskill
   Uppercase: Convert a string to uppercase.
      Params:
      - input: Text to uppercase
        default: ''

   Trim: Trim whitespace from the start and end of a string.
      Params:
      - input: Text to edit
        default: ''

   TrimStart: Trim whitespace from the start of a string.
      Params:
      - input: Text to edit
        default: ''

   TrimEnd: Trim whitespace from the end of a string.
      Params:
      - input: Text to edit
        default: ''

   Lowercase: Convert a string to lowercase.
      Params:
      - input: Text to lowercase
        default: ''

*****************************************
***** Semantic skills and functions *****
*****************************************

Skill: _GLOBAL_FUNCTIONS_
   funcce97d27e3d0b4897acf6122e41430695: Generic function, unknown purpose
      Params:
      - input:
        default: ''

Skill: Writing
   Novel: Write a bedtime story
      Params:
      - input:
        default: ''
      - language:
        default: ''

Skill: SummarizeSkill
   Topics: Analyze given text or document and extract key topics worth remembering
      Params:
      - input:
        default: ''

   Summarize: Summarize given text or any text document
      Params:
      - input: Text to summarize
        default: ''

   MakeAbstractReadable: Given a scientific white paper abstract, rewrite it to make it more readable
      Params:
      - input:
        default: ''

   TopicsMore: Generate list of topics for long length content
      Params:
      - input: Block of text to analyze
        default: ''
      - previousResults: List of topics found from previous blocks of text
        default: ''

   Notegen: Automatically generate compact notes for any text or text document.
      Params:
      - input:
        default: ''

   ActionItems: unknown function

   SummarizeMore: Summarize given text or any text document
      Params:
      - input: Block of text to analyze
        default: ''
      - previousResults: Overview generated from previous blocks of text
        default: ''
      - conversationType: Text type, e.g. chat, email thread, document
        default: ''

*/
#pragma warning restore CS1587 // XML comment is not placed on a valid language element
