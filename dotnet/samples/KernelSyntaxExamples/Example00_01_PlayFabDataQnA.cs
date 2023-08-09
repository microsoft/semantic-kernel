// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.SkillDefinition;
using RepoUtils;

public enum PlannerType
{
    Stepwise,
    ChatStepwise,
    SimpleAction
}

// ReSharper disable once InconsistentNaming
public static partial class Example00_01_PlayFabDataQnA
{
    public static async Task RunAsync()
    {
        string[] questions = new string[]
        {
            "Is my daily active users better or worse than it was last week?",
            "If the number of monthly active players in France increases by 30%, what would be the percentage increase to the overall monthly active players?",
            "How many players played my game yesterday?",
            "What is the average number of players I had last week excluding Friday and Monday?",
            "Is my game doing better in USA or in China?"
        };

        PlannerType[] planners = new[]
        {
            // PlannerType.Stepwise,
            // PlannerType.ChatStepwise,
            PlannerType.SimpleAction
        };

        foreach (string question in questions)
        {
            foreach (PlannerType planner in planners)
            {
                await Console.Out.WriteLineAsync("--------------------------------------------------------------------------------------------------------------------");
                await Console.Out.WriteLineAsync("Planner: " + planner);
                await Console.Out.WriteLineAsync("Question: " + question);
                await Console.Out.WriteLineAsync("--------------------------------------------------------------------------------------------------------------------");

                IKernel kernel = await GetKernelAsync();

                try
                {
                    await RunWithQuestion(kernel, question, PlannerType.SimpleAction);
                }
                catch (Exception e)
                {
                    Console.WriteLine(e);
                }
            }
        }
    }

    private static async Task RunWithQuestion(IKernel kernel, string question, PlannerType plannerType)
    {
        kernel.ImportSkill(new InlineDataProcessorSkill(kernel.Memory), "InlineDataProcessor");

        // Maybe with gpt4 we can add more skills and make them more granular. Planners are instable with Gpt3.5 and complex analytic stesps.
        // kernel.ImportSkill(new GameReportFetcherSkill(kernel.Memory), "GameReportFetcher");
        // kernel.ImportSkill(new LanguageCalculatorSkill(kernel), "advancedCalculator");
        // var bingConnector = new BingConnector(TestConfiguration.Bing.ApiKey);
        // var webSearchEngineSkill = new WebSearchEngineSkill(bingConnector);
        // kernel.ImportSkill(webSearchEngineSkill, "WebSearch");
        // kernel.ImportSkill(new SimpleCalculatorSkill(kernel), "basicCalculator");
        // kernel.ImportSkill(new TimeSkill(), "time");

        Plan plan;
        Stopwatch sw = Stopwatch.StartNew();
        if (plannerType == PlannerType.SimpleAction)
        {
            var planner = new ActionPlanner(kernel);
            plan = await planner.CreatePlanAsync(question);
        }
        else if (plannerType == PlannerType.ChatStepwise)
        {
            var plannerConfig = new Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlannerConfig();
            plannerConfig.ExcludedFunctions.Add("TranslateMathProblem");
            plannerConfig.MinIterationTimeMs = 1500;
            plannerConfig.MaxTokens = 12000;

            ChatStepwisePlanner planner = new(kernel, plannerConfig);

            plan = planner.CreatePlan(question);
        }
        else if (plannerType == PlannerType.Stepwise)
        {
            var plannerConfig = new Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlannerConfig();
            plannerConfig.ExcludedFunctions.Add("TranslateMathProblem");
            plannerConfig.MinIterationTimeMs = 1500;
            plannerConfig.MaxTokens = 1500;

            StepwisePlanner planner = new(kernel, plannerConfig);

            plan = planner.CreatePlan(question);
        }
        else
        {
            throw new NotSupportedException($"[{plannerType}] Planner type is not supported.");
        }

        SKContext result = await plan.InvokeAsync(kernel.CreateNewContext());
        Console.WriteLine("Result: " + result);
        if (result.Variables.TryGetValue("stepCount", out string? stepCount))
        {
            Console.WriteLine("Steps Taken: " + stepCount);
        }

        if (result.Variables.TryGetValue("skillCount", out string? skillCount))
        {
            Console.WriteLine("Skills Used: " + skillCount);
        }

        Console.WriteLine("Time Taken: " + sw.Elapsed);
        Console.WriteLine("*****************************************************");
    }

    private static async Task<IKernel> GetKernelAsync()
    {
        var builder = new KernelBuilder();

        if (!string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.ChatDeploymentName))
        {
            builder = builder.WithAzureChatCompletionService(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey,
                alsoAsTextCompletion: true,
                setAsDefault: true);
        }

        if (!string.IsNullOrEmpty(TestConfiguration.AzureOpenAI.DeploymentName))
        {
            builder = builder.WithAzureTextCompletionService(
                TestConfiguration.AzureOpenAI.DeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey);
        }

        var kernel = builder
            .WithLogger(ConsoleLogger.Logger)
            .WithAzureTextEmbeddingGenerationService(
                deploymentName: "text-embedding-ada-002",
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey)
            .WithMemoryStorage(new VolatileMemoryStore())
            .Configure(c => c.SetDefaultHttpRetryConfig(new HttpRetryConfig
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true,
                MinRetryDelay = TimeSpan.FromSeconds(3),
            }))
            .Build();

        // We're using volotile memory, so pre-load it with data
        await InitializeMemoryAsync(kernel);

        return kernel;
    }

    private static async Task InitializeMemoryAsync(IKernel kernel)
    {
        DateTime today = DateTime.UtcNow;

        string weeklyReport = $"""
The provided CSV table contains weekly aggregated data related to the user activity and retention for a gaming application on the week of August 4, 2023.
This data is broken down by different geographic regions, including France, Greater China, Japan, United Kingdom, United States, Latin America, India, Middle East & Africa, Germany, Canada, Western Europe, Asia Pacific, and Central & Eastern Europe.
Each row represents a different geographic regions, and the columns contain specific metrics related to user engagement.
Below is the description of each field in the table:
- Date: The date for which the data is recorded
- Region: The geographic region to which the data pertains.Examples include Greater China, France, Japan, United Kingdom, United States, Latin America, India, Middle East & Africa, Germany, Canada, Western Europe, Asia Pacific, and Central & Eastern Europe.
- MonthlyActiveUsers: The total number of unique users who engaged with the game at least once during the month
- DailyActiveUsers: The total number of unique users who engaged with the game on August 4, 2023.
- NewPlayers: The number of new users who joined and engaged with the game on August 4, 2023.
- Retention1Day: The percentage of users who returned to the game on the day after their first engagement(August 4, 2023).
- Retention7Day: The percentage of users who returned to the game seven days after their first engagement(August 4, 2023).
Date,Region,MonthlyActiveUsers,DailyActiveUsers,NewPlayers,Retention1Day,Retention7Day
{today:yyyy/MM/dd},Greater China,2059256,292000,37733,5.4,3.03
{today:yyyy/MM/dd},France,975300,302497,5029,13.69,8.26
{today:yyyy/MM/dd},Japan,965110,321652,6394,10.83,7.21
{today:yyyy/MM/dd},United Kingdom,802591,239125,4885,12.37,7.29
{today:yyyy/MM/dd},United States,4624050,1454545,30046,13.66,8.21
{today:yyyy/MM/dd},Latin America,2910856,417127,38295,9.25,5.51
{today:yyyy/MM/dd},India,1257550,115146,21236,7.09,3.37
{today:yyyy/MM/dd},Middle East &Africa,2247499,281922,29776,9.42,4.98
{today:yyyy/MM/dd},Germany,1380647,456723,6222,14.19,8.72
{today:yyyy/MM/dd},Canada,600845,208641,3344,14.33,8.8
{today:yyyy/MM/dd},Western Europe,2451426,720703,15013,12.28,7.37
{today:yyyy/MM/dd},Asia Pacific,2234259,344618,31704,7.94,4.5
{today:yyyy/MM/dd},Central & Eastern Europe,2674562,625276,21676,10.12,6.16
""";

        string weeklyReportWorldWide = $"""
The provided CSV table contains weekly worldwide aggregated data related to the user activity and retention for a gaming application on the week of August 4, 2023.
There is a single row representing worldwide data, and the columns contain specific metrics related to user engagement.
Below is the description of each field in the table:
- Date: The date for which the data is recorded
- MonthlyActiveUsers: The total number of unique users who engaged with the game at least once during the month
- DailyActiveUsers: The total number of unique users who engaged with the game on August 4, 2023.
- NewPlayers: The number of new users who joined and engaged with the game on August 4, 2023.
- Retention1Day: The percentage of users who returned to the game on the day after their first engagement(August 4, 2023).
- Retention7Day: The percentage of users who returned to the game seven days after their first engagement(August 4, 2023).
Date,MonthlyActiveUsers,DailyActiveUsers,NewPlayers,Retention1Day,Retention7Day
{today:yyyy/MM/dd},24916479,5772155,251214,9.5,5.51
""";

        string dauReport = $"""
The provided CSV table contains daily data related to the user activity and game faily active users(DAU) for the last eight days.Each row represents the number of unique users in that day:
Date,DailyActiveUsers
{today:yyyy/MM/dd},5772155
{today.AddDays(-1):yyyy/MM/dd},5762155
{today.AddDays(-2):yyyy/MM/dd},5764155
{today.AddDays(-3):yyyy/MM/dd},5765155
{today.AddDays(-4):yyyy/MM/dd},5765125
{today.AddDays(-5):yyyy/MM/dd},5465155
{today.AddDays(-6):yyyy/MM/dd},4865155
{today.AddDays(-7):yyyy/MM/dd},4864155
{today.AddDays(-8):yyyy/MM/dd},4565255
""";

        await kernel.Memory.SaveInformationAsync(
            collection: "TitleID-Reports",
            text: weeklyReport,
            id: "Weekly_Report");

        await kernel.Memory.SaveInformationAsync(
            collection: "TitleID-Reports",
            text: weeklyReportWorldWide,
            id: "WeeklyWorldwide_Report");

        await kernel.Memory.SaveInformationAsync(
            collection: "TitleID-Reports",
            text: dauReport,
            id: "DAU_Report");
    }
}

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
            MaxTokens = 15000,
            NucleusSamplingFactor = 1f,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
        };

        Response<ChatCompletions> response = await this._openAIClient.GetChatCompletionsAsync(
            deploymentOrModelName: TestConfiguration.AzureOpenAI.ChatDeploymentName, chatCompletion);

        // Path to the Python executable
        string pythonPath = "python"; // Use "python3" if on a Unix-like system

        int retry = 0;
        while (retry++ < 3)
        {
            // Inline Python script
            string pythonScript = response.Value.Choices[0].Message.Content;
            if (!pythonScript.Contains("import io"))
            {
                pythonScript = "import io\n\n" + pythonScript;
            }

            pythonScript = pythonScript
                .Trim("```python")
                .Trim("```")
                .Replace("\"", "\\\"")  // Quote so we can run python via commandline 
                .Replace("pd.compat.StringIO(", "io.StringIO("); // Fix common script mistake


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
            string error = process.StandardError.ReadToEnd().Trim();


            // Wait for the process to finish
            process.WaitForExit();

            // If there are errors in the script, try to fix them
            if (!string.IsNullOrEmpty(error))
            {
                Console.WriteLine("Error in script: " + error);
                chatCompletion.Messages.Add(new ChatMessage(ChatRole.Assistant, pythonScript));
                chatCompletion.Messages.Add(new ChatMessage(ChatRole.User, FixPythonScriptPrompt.Replace("{{$error}}", error)));

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
}

public static class StringHelper
{
    public static string Trim(this string source, string wordToRemove)
    {
        // Remove from the beginning
        while (source.StartsWith(wordToRemove, StringComparison.OrdinalIgnoreCase))
        {
            source = source.Substring(wordToRemove.Length);
        }

        // Remove from the end
        while (source.EndsWith(wordToRemove, StringComparison.OrdinalIgnoreCase))
        {
            source = source.Substring(0, source.Length - wordToRemove.Length);
        }

        return source;
    }
}
