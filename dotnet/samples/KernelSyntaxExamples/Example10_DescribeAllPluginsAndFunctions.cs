// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Plugins.Core;
using Plugins;
using RepoUtils;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example10_DescribeAllPluginsAndFunctions : BaseTest
{
    /// <summary>
    /// Print a list of all the functions imported into the kernel, including function descriptions,
    /// list of parameters, parameters descriptions, etc.
    /// See the end of the file for a sample of what the output looks like.
    /// </summary>
    [Fact]
    public Task RunAsync()
    {
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

        WriteLine("**********************************************");
        WriteLine("****** Registered plugins and functions ******");
        WriteLine("**********************************************");
        WriteLine();

        foreach (KernelFunctionMetadata func in functions)
        {
            PrintFunction(func);
        }

        return Task.CompletedTask;
    }

    private void PrintFunction(KernelFunctionMetadata func)
    {
        WriteLine($"Plugin: {func.PluginName}");
        WriteLine($"   {func.Name}: {func.Description}");

        if (func.Parameters.Count > 0)
        {
            WriteLine("      Params:");
            foreach (var p in func.Parameters)
            {
                WriteLine($"      - {p.Name}: {p.Description}");
                WriteLine($"        default: '{p.DefaultValue}'");
            }
        }

        WriteLine();
    }

    public Example10_DescribeAllPluginsAndFunctions(ITestOutputHelper output) : base(output)
    {
    }
}

/** Sample output:

**********************************************
****** Registered plugins and functions ******
**********************************************

Plugin: StaticTextPlugin
   Uppercase: Change all string chars to uppercase
      Params:
      - input: Text to uppercase
        default: ''

Plugin: StaticTextPlugin
   AppendDay: Append the day variable
      Params:
      - input: Text to append to
        default: ''
      - day: Value of the day to append
        default: ''

Plugin: AnotherTextPlugin
   Trim: Trim whitespace from the start and end of a string.
      Params:
      - input:
        default: ''

Plugin: AnotherTextPlugin
   TrimStart: Trim whitespace from the start of a string.
      Params:
      - input:
        default: ''

Plugin: AnotherTextPlugin
   TrimEnd: Trim whitespace from the end of a string.
      Params:
      - input:
        default: ''

Plugin: AnotherTextPlugin
   Uppercase: Convert a string to uppercase.
      Params:
      - input:
        default: ''

Plugin: AnotherTextPlugin
   Lowercase: Convert a string to lowercase.
      Params:
      - input:
        default: ''

Plugin: AnotherTextPlugin
   Length: Get the length of a string.
      Params:
      - input:
        default: ''

Plugin: AnotherTextPlugin
   Concat: Concat two strings into one.
      Params:
      - input: First input to concatenate with
        default: ''
      - input2: Second input to concatenate with
        default: ''

Plugin: AnotherTextPlugin
   Echo: Echo the input string. Useful for capturing plan input for use in multiple functions.
      Params:
      - text: Input string to echo.
        default: ''

Plugin: SummarizePlugin
   MakeAbstractReadable: Given a scientific white paper abstract, rewrite it to make it more readable
      Params:
      - input:
        default: ''

Plugin: SummarizePlugin
   Notegen: Automatically generate compact notes for any text or text document.
      Params:
      - input:
        default: ''

Plugin: SummarizePlugin
   Summarize: Summarize given text or any text document
      Params:
      - input: Text to summarize
        default: ''

Plugin: SummarizePlugin
   Topics: Analyze given text or document and extract key topics worth remembering
      Params:
      - input:
        default: ''

*/
