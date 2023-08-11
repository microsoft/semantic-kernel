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

namespace PlayFabExamples.Example01_DataQnA;

public class InlineDataProcessorSkill
{
    #region Static Data
    /// <summary>
    /// The system prompt for a chat that creates python scripts to solve analytic problems
    /// </summary>
    private static readonly string CreatePythonScriptSystemPrompt = @"
You're a python script programmer. 
Once you get a question, write a Python script that loads the comma-separated (CSV) data inline (within the script) into a dataframe.
The CSV data should not be assumed to be available in any external file.
Only load the data from [Input CSV]. do not attempt to initialize the data frame with any additional rows.
The script should:
- Attempt to answer the provided question and print the output to the console as a user-friendly answer.
- Print facts and calculations that lead to this answer
- Import any necessary modules within the script (e.g., import datetime if used)
- If the script needs to use StringIO, it should import io, and then use it as io.StringIO (To avoid this error: module 'pandas.compat' has no attribute 'StringIO')
The script can use one or more of the provided inline scripts and should favor the ones relevant to the question.

Simply output the final script below without anything beside the code and its inline documentation.
Never attempt to calculate the MonthlyActiveUsers as a sum of DailyActiveUsers since DailyActiveUsers only gurantees the user uniqueness within a single day

[Input CSV]
{{$inlineData}}

";

    /// <summary>
    /// The user agent prompt for fixing a python script that has runtime errors
    /// </summary>
    private static readonly string FixPythonScriptPrompt = @"
The following python error has encountered while running the script above.
Fix the script so it has no errors.
Make the minimum changes that are required. If you need to use StringIO, make sure to import io, and then use it as io.StringIO
simply output the final script below without any additional explanations.

[Error]
{{$error}}

[Fixed Script]
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
        StringBuilder stringBuilder = new();
        var memories = _memory.SearchAsync("TitleID-Reports", question, limit: 2, minRelevanceScore: 0.65);
        int idx = 1;
        await foreach (MemoryQueryResult memory in memories)
        {
            stringBuilder.AppendLine($"[Input CSV {idx++}]");
            stringBuilder.AppendLine(memory.Metadata.Text);
            stringBuilder.AppendLine();
        }

        string csvData = stringBuilder.ToString();
        string ret = await CreateAndExcecutePythonScript(question, csvData);
        return ret;
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
        DateTime today = DateTime.UtcNow;

        var chatCompletion = new ChatCompletionsOptions()
        {
            Messages =
                {
                    new ChatMessage(ChatRole.System, CreatePythonScriptSystemPrompt.Replace("{{$inlineData}}", inlineData)),
                    new ChatMessage(ChatRole.User, question + "\nPrint facts and calculations that lead to this answer\n[Python Script]")
                },
            Temperature = 0.1f,
            MaxTokens = 8000,
            NucleusSamplingFactor = 1f,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
        };

        Azure.Response<ChatCompletions> response = await this._openAIClient.GetChatCompletionsAsync(
            deploymentOrModelName: TestConfiguration.AzureOpenAI.ChatDeploymentName, chatCompletion);

        // Path to the Python executable
        string pythonPath = "python"; // Use "python3" if on a Unix-like system

        int retry = 0;
        while (retry++ < 3)
        {
            // Inline Python script
            string pythonScript = response.Value.Choices[0].Message.Content;
            pythonScript = GetScriptOnly(pythonScript)
                .Replace("\"", "\\\"")  // Quote so we can run python via commandline 
                .Replace("pd.compat.StringIO(", "io.StringIO("); // Fix common script mistake

            if (!pythonScript.Contains("import io"))
            {
                pythonScript = "import io\n\n" + pythonScript;
            }

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
                chatCompletion.Messages.Add(new ChatMessage(ChatRole.Assistant, pythonScript));
                chatCompletion.Messages.Add(new ChatMessage(ChatRole.User, FixPythonScriptPrompt.Replace("{{$error}}", warningsAndErrors)));

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
