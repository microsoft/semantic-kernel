// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics;
using System.Text;
using Azure.AI.OpenAI;
using Azure;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using PlayFabExamples.Common.Configuration;
using System.Text.Json;
using PlayFabExamples.Example01_DataQnA.Reports;

namespace PlayFabExamples.Example01_DataQnA;

public class InlineDataProcessorSkill
{
    #region Static Data
    /// <summary>
    /// The system prompt for a chat that creates python scripts to solve analytic problems
    /// </summary>
    private static readonly string CreatePythonScriptSystemPrompt = @"
You're a python script programmer and also data-driven descision maker.
Your answers are also in the form of python script that can be compiled and without additional text except the script itself.
The python script itself should prints to screen detailed explanation of it got to the answer using the 'print' method.
Once you get a question, write a Python script that uses one or more of the data-frames loaded in [Input DataFrames] below and provides an answer.
Only load the data from [Input DataFrames]. do not attempt to initialize other data frames and do not assume any other columns other than what documented below.
The script should:
- Attempt to answer the provided question and print the output to the console as a user-friendly answer.
- Print intermediate calculations that lead to this answer
- Import any necessary modules within the script (e.g., import datetime if used)
- If the script needs to use StringIO, it should import io, and then use it as io.StringIO (To avoid this error: module 'pandas.compat' has no attribute 'StringIO')
The script can use one or more of the provided dataframes and should favor [Input DataFrame 1] (and only use [Input DataFrames 2] if absolutely needed).

Simply output the final script below without anything beside the code and its inline documentation.
Never attempt to calculate the MonthlyActiveUsers as a sum of DailyActiveUsers since DailyActiveUsers only gurantees the user uniqueness within a single day.
Do not assume certain order of the dataframe. Always sort the data frame by the relevant columns before using it.
Date columns are string formatted so you need to convert them to datetime before using them.

Today Date: {{$date.today}}

[Input DataFrames]
{{$inlineData}}

";

    /// <summary>
    /// The user agent prompt for fixing a python script that has runtime errors
    /// </summary>
    private static readonly string FixPythonScriptPrompt = @"
The python script had an error. Fix the script so it has no errors.
Make the minimum changes that are required.
simply output the final script below without any additional explanations.

[Error]
{{$error}}

[Fixed Script]
{{$scriptPrefix}}
";
    #endregion

    #region Data Members
    /// <summary>
    /// The semantic memory containing relevant reports needed to solve the provided question
    /// </summary>
    private readonly ISemanticTextMemory _memory;

    /// <summary>
    /// An open AI client
    /// </summary>
    private readonly OpenAIClient _openAIClient;
    #endregion

    #region Constructor
    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="memory">The semantic memory containing relevant reports needed to solve the provided question</param>
    public InlineDataProcessorSkill(ISemanticTextMemory memory)
    {
        this._memory = memory ?? throw new ArgumentNullException(nameof(memory));
        _openAIClient = new(
            new Uri(TestConfiguration.AzureOpenAI.Endpoint),
            new AzureKeyCredential(TestConfiguration.AzureOpenAI.ApiKey));
    }
    #endregion

    #region Public Methods
    [SKFunction,
    SKName("GetAnswerForGameQuestion"),
    Description("Answers questions about game's data and its players around engagement, usage, time spent and game analytics")]
    public async Task<string> GetAnswerForGameQuestionAsync(
        [Description("The question related to the provided inline data.")]
        string question,
        SKContext context)
    {
        StringBuilder systemMessageInlineData = new();
        IAsyncEnumerable<MemoryQueryResult> memories = _memory.SearchAsync("TitleID-Reports", question, limit: 2, minRelevanceScore: 0.7);
        int idx = 1;

        StringBuilder pythonScriptScriptPrefix = new ();
        pythonScriptScriptPrefix.AppendLine("import io");
        pythonScriptScriptPrefix.AppendLine("import pandas as pd");
        pythonScriptScriptPrefix.AppendLine();

        StringBuilder pythonScriptScriptActualPrefix = new ();
        pythonScriptScriptActualPrefix.AppendLine("import io");
        pythonScriptScriptActualPrefix.AppendLine("import pandas as pd");
        pythonScriptScriptActualPrefix.AppendLine();


        await foreach (MemoryQueryResult memory in memories)
        {
            PlayFabReport playFabReport = JsonSerializer.Deserialize<PlayFabReport>(memory.Metadata.AdditionalMetadata);

            systemMessageInlineData.AppendLine($"[DataFrame {idx++}]");
            systemMessageInlineData.AppendLine(playFabReport.GetDetailedDescription());
            systemMessageInlineData.AppendLine($"{playFabReport.ReportName} = pd.read_csv('{playFabReport.ReportName}.csv')");
            systemMessageInlineData.AppendLine();

            pythonScriptScriptPrefix.AppendLine($"# Columns in DataFrame: {playFabReport.GetCsvHeader()}");
            pythonScriptScriptPrefix.AppendLine($"{playFabReport.ReportName} = pd.read_csv('{playFabReport.ReportName}.csv')");
            pythonScriptScriptPrefix.AppendLine();

            string inlineCsvData = $"io.StringIO('''{playFabReport.GetCsvHeader()}\n{playFabReport.CsvData}''')";
            pythonScriptScriptActualPrefix.AppendLine($"{playFabReport.ReportName} = pd.read_csv({inlineCsvData})");
            pythonScriptScriptActualPrefix.AppendLine();
        }

        var chatCompletion = new ChatCompletionsOptions()
        {
            Messages =
                {
                    new ChatMessage(
                        ChatRole.System,
                        CreatePythonScriptSystemPrompt
                            .Replace("{{$inlineData}}", systemMessageInlineData.ToString())
                            .Replace("{{$date.today}}", DateTime.UtcNow.ToString("yyyy/MM/dd"))),
                    new ChatMessage(ChatRole.User, $"\n# Python script that print an answer to this question '{question}\n# It also prints facts and calculations that lead the answer\n\n{pythonScriptScriptPrefix}")
                },
            Temperature = 0.05f,
            MaxTokens = 8000,
            NucleusSamplingFactor = 1f,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
        };

        Azure.Response<ChatCompletions> response = await this._openAIClient.GetChatCompletionsAsync(
            deploymentOrModelName: TestConfiguration.AzureOpenAI.ChatDeploymentName, chatCompletion);

        int retry = 0;
        while (retry++ < 3)
        {
            // Inline Python script
            string pythonScript =
                (pythonScriptScriptActualPrefix.ToString() + Environment.NewLine + GetScriptOnly(response.Value.Choices[0].Message.Content)
                .Replace("\"", "\\\"")  // Quote so we can run python via commandline 
                .Replace("pd.compat.StringIO(", "io.StringIO(")); // Fix common script mistake

            // Path to the Python executable
            string pythonPath = "python"; // Use "python3" if on a Unix-like system

            // Create a ProcessStartInfo and set the required properties
            var startInfo = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = "-c \"" + pythonScript + "\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            // Create a new Process
            using Process process = new() { StartInfo = startInfo };

            // Start the Python process
            process.Start();

            // Read the Python process output and error
            string output = process.StandardOutput.ReadToEnd().Trim();
            string warningsAndErrors = process.StandardError.ReadToEnd().Trim();

            // Wait for the process to finish
            process.WaitForExit();

            // If there are errors in the script, try to fix them
            if (process.ExitCode != 0)
            {
                Console.WriteLine("Error in script: " + warningsAndErrors);
                chatCompletion.Messages.Add(new ChatMessage(
                    ChatRole.Assistant,
                    $"{pythonScriptScriptPrefix}\n{response.Value.Choices[0].Message.Content}"));
                chatCompletion.Messages.Add(new ChatMessage(
                    ChatRole.User,
                    FixPythonScriptPrompt
                        .Replace("{{$error}}", warningsAndErrors)
                        .Replace("{{$scriptPrefix}}", pythonScriptScriptPrefix.ToString())));

                response = await this._openAIClient.GetChatCompletionsAsync(
                    deploymentOrModelName: TestConfiguration.AzureOpenAI.ChatDeploymentName, chatCompletion);
            }
            else
            {
                return output;
            }
        }

        return "Couldn't get an answer";

    }
    #endregion

    #region Private Methods
    /// <summary>
    /// Creates and executes a python script to get an answer for an analytic question
    /// </summary>
    /// <param name="question">The analytic question</param>
    /// <param name="inlineData">The data that can be used to answer the given question (e.g: can be list of CSV reports)</param>
    /// <returns>The final answer</returns>
    private async Task<string> CreateAndExcecutePythonScript(string question, string inlineData)
    {
        return null;
    }

    private string GetScriptOnly(string pythonScript)
    {
        const string startMarker = "```python";
        const string endMarker = "```";

        string ret = pythonScript;
        int startIndex = pythonScript.IndexOf(startMarker) + startMarker.Length;
        int endIndex = pythonScript.LastIndexOf(endMarker);

        if (startIndex >= 0 && endIndex > startIndex)
        {
            ret = pythonScript.Substring(startIndex, endIndex - startIndex);
        }

        return ret;
    }

    #endregion
}
