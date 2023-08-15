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
using System.Text.RegularExpressions;

namespace PlayFabExamples.Example01_DataQnA;

public class InlineDataProcessorSkill
{
    #region Static Data
    /// <summary>
    /// The system prompt for a chat that creates python scripts to solve analytic problems
    /// </summary>
    private static readonly string CreatePythonScriptSystemPrompt = @"
You're a python script programmer that write code to answer business questions.
The python script should use the print() function to output to screen the following details in a user-friendly message:
- First start by printing the final answer to the question.
- Print additional explanation and intermediate results that led to the final answer.
The python script that uses one or more of the data-frames loaded in [Input DataFrames] below and should favor using the one under [Input DataFrame 1].
Do not attempt to initialize other data frames and do not assume any other columns other than what documented below.
The script should:
- Attempt to answer the provided question and print the output to the console as a user-friendly answer.
- Print intermediate calculations and chain of thought that lead to this answer
- Import any necessary modules within the script (e.g., import datetime if used)
- If the script needs to use StringIO, it should import io, and then use it as io.StringIO (To avoid this error: module 'pandas.compat' has no attribute 'StringIO')

Never attempt to calculate the MonthlyActiveUsers as a sum of DailyActiveUsers since DailyActiveUsers only guarantees the user uniqueness within a single day.
Do not assume certain order of the data-frame. Always sort the data-frame by the relevant columns before using it.
Date columns are string formatted so you need to convert them to datetime before using them.

Today Date: {{$date.today}}

[Input DataFrames]
{{$inlineData}}
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

        List<PlayFabReport> playFabReports = new();
        StringBuilder pythonScriptScriptActualPrefix = new();
        await foreach (MemoryQueryResult memory in memories)
        {
            PlayFabReport playFabReport = JsonSerializer.Deserialize<PlayFabReport>(memory.Metadata.AdditionalMetadata);
            playFabReports.Add(playFabReport);

            systemMessageInlineData.AppendLine($"[DataFrame {idx++}]");
            systemMessageInlineData.AppendLine(playFabReport.GetDetailedDescription());
            systemMessageInlineData.AppendLine($"{playFabReport.ReportName} = pd.read_csv('{playFabReport.ReportName}.csv')");
            systemMessageInlineData.AppendLine();
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
                    new ChatMessage(ChatRole.User, question)
                },
            Temperature = 0.1f,
            MaxTokens = 8000,
            NucleusSamplingFactor = 0f,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
        };

        int retry = 0;
        while (retry++ < 3)
        {
            Azure.Response<ChatCompletions> response = await this._openAIClient.GetChatCompletionsAsync(
            deploymentOrModelName: TestConfiguration.AzureOpenAI.ChatDeploymentName, chatCompletion);

            string rawResponse = response.Value.Choices.Single().Message.Content;
            string pythonScript = ExtractPythonScript(rawResponse);
            pythonScript = AddMissingDataFrames(pythonScript, playFabReports);
            pythonScript = AddMissingImports(pythonScript);

            string pythonScriptWithInlinedData = InlineDataFramesData(pythonScript, playFabReports);

            // Inline Python script
            pythonScriptWithInlinedData = pythonScriptWithInlinedData
                .Replace("\"", "\\\"")  // Quote so we can run python via commandline 
                .Replace("pd.compat.StringIO(", "io.StringIO("); // Fix common script mistake

            // Path to the Python executable
            string pythonPath = "python"; // Use "python3" if on a Unix-like system

            // Create a ProcessStartInfo and set the required properties
            var startInfo = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = "-c \"" + pythonScriptWithInlinedData + "\"",
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
                chatCompletion.Messages.Add(new ChatMessage(ChatRole.Assistant, pythonScript));
                chatCompletion.Messages.Add(new ChatMessage(
                    ChatRole.User,
                    "The following error/s occured. Can you write the fixed script? " + Environment.NewLine + warningsAndErrors));
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

    private string ExtractPythonScript(string inputText)
    {
        // Extract Python script using regular expressions
        string pattern = @"```(?:\s*)python(.*?)```";
        MatchCollection matches = Regex.Matches(inputText, pattern, RegexOptions.Singleline);

        if (matches.Count == 0)
        {
            return inputText;
        }

        StringBuilder ret = new();
        foreach (Match match in matches)
        {
            string pythonScript = match.Groups[1].Value.Trim();
            ret.AppendLine(pythonScript);
            ret.AppendLine();
        }

        return ret.ToString();
    }

    private string AddMissingDataFrames(string pythonScript, List<PlayFabReport> playFabReports)
    {
        bool hadMissingDataFrames = false;
        foreach (PlayFabReport report in playFabReports)
        {
            bool isFirstMissing = true;
            if (pythonScript.Contains(report.ReportName) && !pythonScript.Contains($"'{report.ReportName}.csv'"))
            {
                if (isFirstMissing)
                {
                    isFirstMissing = false;
                    pythonScript = Environment.NewLine + pythonScript;
                }

                pythonScript = $"{report.ReportName} = pd.read_csv('{report.ReportName}.csv')" + Environment.NewLine + pythonScript;
            }
        }

        if (hadMissingDataFrames)
        {
            pythonScript += Environment.NewLine;
        }

        return pythonScript;
    }

    private string AddMissingImports(string pythonScript)
    {
        string[] requiredImports = new[]
        {
            "import pandas as pd",
            "import io"
        };

        // Ensure required imports show up at the top of the script and only once. Move them to the top if needed
        pythonScript = Environment.NewLine + pythonScript;
        foreach (string requiredImport in requiredImports)
        {
            if (pythonScript.Contains(requiredImport))
            {
                pythonScript = pythonScript.Replace(requiredImport, "");
            }

            pythonScript = requiredImport + Environment.NewLine + pythonScript;
        }

        return pythonScript;
    }

    private string InlineDataFramesData(string pythonScript, List<PlayFabReport> playFabReports)
    {
        foreach (var report in playFabReports)
        {
            pythonScript = pythonScript.Replace(
                $"'{report.ReportName}.csv'",
                $"io.StringIO('''{report.GetCsvHeader()}\n{report.CsvData}''')");
        }

        return pythonScript;
    }

    #endregion
}
