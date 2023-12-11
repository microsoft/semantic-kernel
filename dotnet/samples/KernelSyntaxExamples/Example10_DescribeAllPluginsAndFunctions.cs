// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Core;
using Plugins;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example10_DescribeAllPluginsAndFunctions
{
    /// <summary>
    /// Print a list of all the functions imported into the kernel, including function descriptions,
    /// list of parameters, parameters descriptions, etc.
    /// See the end of the file for a sample of what the output looks like.
    /// </summary>
    public static Task RunAsync()
    {
        Console.WriteLine("======== Describe all plugins and functions ========");

        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Import a native plugin
        kernel.ImportPluginFromType<StaticTextPlugin>();

        // Import another native plugin
        kernel.ImportPluginFromType<TextPlugin>("AnotherTextPlugin");

        // Import a semantic plugin
        string folder = RepoFiles.SamplePluginsPath();
        kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "SummarizePlugin"));

        // Define a prompt function inline, without naming
        var sFun1 = kernel.CreateFunctionFromPrompt("tell a joke about {{$input}}", new OpenAIPromptExecutionSettings() { MaxTokens = 150 });

        // Define a prompt function inline, with plugin name
        var sFun2 = kernel.CreateFunctionFromPrompt(
            "write a novel about {{$input}} in {{$language}} language",
            new OpenAIPromptExecutionSettings() { MaxTokens = 150 },
            functionName: "Novel",
            description: "Write a bedtime story");

        var functions = kernel.Plugins.GetFunctionsMetadata();

        Console.WriteLine("*****************************************");
        Console.WriteLine("****** Registered plugins and functions ******");
        Console.WriteLine("*****************************************");
        Console.WriteLine();

        foreach (KernelFunctionMetadata func in functions)
        {
            PrintFunction(func);
        }

        return Task.CompletedTask;
    }

    private static void PrintFunction(KernelFunctionMetadata func)
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
****** Native plugins and functions ******
*****************************************

Plugin: StaticTextPlugin
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

Plugin: TextPlugin
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
***** Semantic plugins and functions *****
*****************************************

Plugin: Writing
   Novel: Write a bedtime story
      Params:
      - input:
        default: ''
      - language:
        default: ''

Plugin: SummarizePlugin
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
