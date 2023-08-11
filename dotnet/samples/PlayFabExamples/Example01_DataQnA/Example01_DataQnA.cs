// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics;
using System.Text;
using Azure.AI.OpenAI;
using Azure;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.Azure.Cosmos;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;
using PlayFabExamples.Common.Configuration;
using PlayFabExamples.Common.Logging;

namespace PlayFabExamples.Example01_DataQnA;

public enum PlannerType
{
    Stepwise,
    ChatStepwise,
    SimpleAction
}

// ReSharper disable once InconsistentNaming
public static partial class Example01_DataQnA
{
    public static Dictionary<string, string> AllTitleReports = null;

    public static async Task RunAsync()
    {
        CancellationToken cancellationToken = CancellationToken.None;
        string[] questions = new string[]
        {
            "What is my 2-days retention average? Was my 2-days retention in the last few days was better or worse than that?",
            "How many players played my game yesterday?",
            "What is the average number of players I had last week excluding Friday and Monday?",
            "Is my game doing better in USA or in China?",
            "If the number of monthly active players in France increases by 30%, what would be the percentage increase to the overall monthly active players?",
            "At which specific times of the day were the highest and lowest numbers of purchases recorded? Please provide the actual sales figures for these particular time slots.",
            "Which three items had the highest total sales and which had the highest revenue generated yesterday?",
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

                IKernel kernel = await GetKernelAsync(cancellationToken);

                try
                {
                    await RunWithQuestionAsync(kernel, question, PlannerType.SimpleAction, cancellationToken);
                }
                catch (Exception e)
                {
                    Console.WriteLine(e);
                }
            }
        }
    }

    private static async Task RunWithQuestionAsync(IKernel kernel, string question, PlannerType plannerType, CancellationToken cancellationToken)
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
            plan = await planner.CreatePlanAsync(question, cancellationToken);
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

        SKContext result = await plan.InvokeAsync(kernel.CreateNewContext(), cancellationToken: cancellationToken);
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
        Console.WriteLine("");
    }

    private static async Task<IKernel> GetKernelAsync(CancellationToken cancellationToken)
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
        await InitializeMemoryAsync(kernel, TestConfiguration.PlayFab.TitleId, cancellationToken);

        return kernel;
    }

    private static async Task InitializeMemoryAsync(IKernel kernel, string titleId, CancellationToken cancellationToken)
    {
        if (AllTitleReports == null)
        {
            DateTime today = DateTime.UtcNow.Date;

            using var reportDataFetcher = new ReportDataFetcher(
                titleId,
                TestConfiguration.PlayFab.ReportsCosmosDBEndpoint,
                TestConfiguration.PlayFab.ReportsCosmosDBKey,
                TestConfiguration.PlayFab.ReportsCosmosDBDatabaseName,
                TestConfiguration.PlayFab.ReportsCosmosDBContainerName);

            IList<GameReport> gameReports = await reportDataFetcher.FetchByQueryAsync(
                $"SELECT * FROM c WHERE c.TitleId='{titleId}' and c.ReportDate>='{today.AddDays(-3):yyyy-MM-dd}'",
                cancellationToken);

            Dictionary<string, GameReport> latestReports = gameReports
              .GroupBy(report => report.ReportName)
              .Select(group => group.OrderByDescending(report => report.ReportDate).First())
              .ToDictionary(report => report.ReportName);

            if (!latestReports.ContainsKey("EngagementMetricsRollupReportCSV"))
            {
                GameReport gameEngagementRollupReport = (await reportDataFetcher.FetchByQueryAsync(
                     $"SELECT TOP 1 * FROM c WHERE c.TitleId='{titleId}' and c.ReportName='EngagementMetricsRollupReportCSV' ORDER BY c.ReportDate DESC",
                    cancellationToken)).FirstOrDefault();
                latestReports.Add(gameEngagementRollupReport.ReportName, gameEngagementRollupReport);
            }

            string dailyOverviewReport =
                DailyOverviewReportRecord.GetDescription() + Environment.NewLine +
                DailyOverviewReportRecord.GetHeader() + Environment.NewLine +
                string.Join(Environment.NewLine,
                    JsonConvert.DeserializeObject<List<DailyOverviewReportRecord>>(latestReports["DailyOverviewReport"].ReportData)
                    .Select(reportData => reportData.AsCsvRow()));

            string rollingThirtyDayOverviewReport =
                RollingThirtyDayOverviewReportRecord.GetDescription() + Environment.NewLine +
                RollingThirtyDayOverviewReportRecord.GetHeader() + Environment.NewLine +
                string.Join(Environment.NewLine,
                    JsonConvert.DeserializeObject<List<RollingThirtyDayOverviewReportRecord>>(latestReports["RollingThirtyDayOverviewReport"].ReportData)
                    .Select(reportData => reportData.AsCsvRow()));

            string dailyTopItemsReportRecord =
                DailyTopItemsReportRecord.GetDescription() + Environment.NewLine +
                DailyTopItemsReportRecord.GetHeader() + Environment.NewLine +
                string.Join(Environment.NewLine,
                    JsonConvert.DeserializeObject<List<DailyTopItemsReportRecord>>(latestReports["DailyTopItemsReport"].ReportData)
                    .Select(reportData => reportData.AsCsvRow()));

            string thirtyDayRetentionReportRecord =
                ThirtyDayRetentionReportRecord.GetDescription() + Environment.NewLine +
                ThirtyDayRetentionReportRecord.GetHeader() + Environment.NewLine +
                string.Join(Environment.NewLine,
                    JsonConvert.DeserializeObject<List<ThirtyDayRetentionReportRecord>>(latestReports["ThirtyDayRetentionReport"].ReportData)
                    .Where(row => row.CohortDate > DateTime.UtcNow.AddDays(-14)) // Filter just last 14 days so it doesn't pass the embedding limit when indexed
                    .Select(reportData => reportData.AsCsvRow()));

            var latestEngagementMetrics =
                latestReports["EngagementMetricsRollupReportCSV"].ReportData
                    .Split("\"", StringSplitOptions.RemoveEmptyEntries).Where(line => line != ",")
                    .Select(line =>
                    {
                        string[] values = line.Split(',');

                        return new EngagementMetricsRollupReportCSVRecord
                        {
                            ReportDate = DateTime.Parse(values[1]),
                            Platform = values[2],
                            Region = values[3],
                            Segment = values[4],
                            MonthlyActiveUsers = int.Parse(values[5]),
                            DailyActiveUsers = int.Parse(values[6]),
                            NewPlayers = int.Parse(values[7]),
                            Retention1Day = double.Parse(values[11]),
                            Retention7Day = double.Parse(values[12]),
                        };
                    })
                    .Where(row => row.Segment == "All" && row.Platform == "All")
                    .ToList();

            DateTime latestEngagmementRolloutReportDate = latestEngagementMetrics.Max(row => row.ReportDate);
            latestEngagementMetrics = latestEngagementMetrics.Where(row => row.ReportDate == latestEngagmementRolloutReportDate).ToList();
            string engagementMetricsRollupReport =
                EngagementMetricsRollupReportCSVRecord.GetDescription() + Environment.NewLine +
                EngagementMetricsRollupReportCSVRecord.GetHeader() + Environment.NewLine +
                string.Join(Environment.NewLine, latestEngagementMetrics.Select(row => row.AsCsvRow()));

            AllTitleReports = new Dictionary<string, string>();
            AllTitleReports.Add("DailyOverviewReport", dailyOverviewReport);
            AllTitleReports.Add("RollingThirtyDayOverviewReport", rollingThirtyDayOverviewReport);
            AllTitleReports.Add("DailyTopItemsReportRecord", dailyTopItemsReportRecord);
            AllTitleReports.Add("ThirtyDayRetentionReportRecord", thirtyDayRetentionReportRecord);
            AllTitleReports.Add("EngagementMetricsRollupReport", engagementMetricsRollupReport);
        }

        foreach (var item in AllTitleReports)
        {
            await kernel.Memory.SaveInformationAsync(
                collection: "TitleID-Reports",
                text: item.Value,
                id: item.Key,
                cancellationToken: cancellationToken);
        }
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

public class ReportDataFetcher : IDisposable
{
    private readonly string _titleId;
    private readonly CosmosClient _cosmosClient;
    private readonly string _databaseName;
    private readonly string _containerName;

    public ReportDataFetcher(string titleId, string endpointUrl, string primaryKey, string databaseName, string containerName)
    {
        this._titleId = titleId ?? throw new ArgumentNullException(nameof(titleId));
        this._cosmosClient = new(
            endpointUrl ?? throw new ArgumentNullException(nameof(endpointUrl)),
            primaryKey ?? throw new ArgumentNullException(nameof(primaryKey)));

        this._databaseName = databaseName ?? throw new ArgumentNullException(nameof(databaseName));
        this._containerName = containerName ?? throw new ArgumentNullException(nameof(containerName));
    }

    public async Task<GameReport> FetchAsync(string documentId, CancellationToken cancellationToken)
    {
        // Get a reference to the database and container
        Database database = this._cosmosClient.GetDatabase(this._databaseName);
        Microsoft.Azure.Cosmos.Container container = database.GetContainer(this._containerName);

        // Read the document by its ID
        ItemResponse<GameReport> response = await container.ReadItemAsync<GameReport>(documentId, new PartitionKey(this._titleId), cancellationToken: cancellationToken);
        return response.Resource;
    }

    public async Task<IList<GameReport>> FetchByQueryAsync(string query, CancellationToken cancellationToken)
    {
        // Get a reference to the database and container
        Database database = this._cosmosClient.GetDatabase(this._databaseName);
        Microsoft.Azure.Cosmos.Container container = database.GetContainer(this._containerName);

        List<GameReport> ret = new();

        // Execute the query
        QueryDefinition queryDefinition = new(query);
        FeedIterator<dynamic> resultSetIterator = container.GetItemQueryIterator<dynamic>(queryDefinition);

        while (resultSetIterator.HasMoreResults)
        {
            FeedResponse<dynamic> response = await resultSetIterator.ReadNextAsync(cancellationToken);
            foreach (dynamic item in response)
            {
                GameReport? gameReport = ((JObject)item).ToObject<GameReport>();
                if (gameReport is not null)
                {
                    ret.Add(gameReport);
                }
            }
        }

        return ret;
    }

    public void Dispose()
    {
        this._cosmosClient.Dispose();
    }
}

public class GameReport
{
    public DateTime ReportDate { get; set; }
    public required string ReportId { get; set; }
    public required string ReportName { get; set; }
    public required string ReportData { get; set; }
}

public class DailyOverviewReportRecord
{
    public static string GetHeader() =>
        "Timestamp,TotalLogins,UniqueLogins,UniquePayers,Revenue,Purchases,TotalCalls,TotalSuccessfulCalls,TotalErrors,Arpu,Arppu,AvgPurchasePrice,NewUsers";

    public string AsCsvRow() =>
        $"{this.Timestamp},{this.TotalLogins},{this.UniqueLogins},{this.UniquePayers},{this.Revenue},{this.Purchases},{this.TotalCalls},{this.TotalSuccessfulCalls},{this.TotalErrors},{this.Arpu},{this.Arppu},{this.AvgPurchasePrice},{this.NewUsers}";

    public static string GetDescription() =>
        """
        The provided CSV table contains granular daily data capturing game reports for each hour, offering valuable insights into player engagement, financial performance, and the overall gameplay experience.
        This dataset offers a comprehensive view into player behavior, enabling data-driven decisions to enhance gameplay, optimize monetization strategies, and improve overall player satisfaction.
        Through its hour-by-hour breakdown, it allows for precise analysis of temporal patterns, aiding in understanding player dynamics over different times of the day.
        The report has 24 rows where every row reprsents one hour of the day.
        Description of Columns:
        - Timestamp: The date and time of a one-hour window when the report was compiled, presented in Coordinated Universal Time (UTC).
        - TotalLogins: The aggregate count of player logins during the specified hour, revealing the volume of player interactions.
        - UniqueLogins: The distinct number of players who logged into the game within the same hour, indicating individual engagement.
        - UniquePayers: The count of unique players who conducted in-game purchases, reflecting the game's monetization reach.
        - Revenue: The cumulative revenue in dollars generated from in-game purchases throughout the hour, demonstrating financial performance.
        - Purchases: The total number of in-game transactions carried out by players in the specified hour.
        - TotalCalls: The collective sum of player-initiated interactions, encompassing gameplay actions, API requests, and more..
        - TotalSuccessfulCalls: The count of interactions that succeeded without encountering errors, highlighting player satisfaction.
        - TotalErrors: The overall number of errors encountered during interactions, potential indicators of player experience challenges.
        - Arpu (Average Revenue Per User): The average revenue generated per unique player, calculated as Revenue / UniquePayers.
        - Arppu (Average Revenue Per Paying User): The average revenue generated per player who made purchases, calculated as Revenue / UniquePayers.
        - AvgPurchasePrice: The average price of in-game purchases made by players, calculated as Revenue / Purchases.
        - NewUsers: The count of new players who started engaging with the game during the specified hour period.
        """;

    public DateTime Timestamp { get; set; }
    public int TotalLogins { get; set; }
    public int UniqueLogins { get; set; }
    public int UniquePayers { get; set; }
    public decimal Revenue { get; set; }
    public int Purchases { get; set; }
    public long TotalCalls { get; set; }
    public long TotalSuccessfulCalls { get; set; }
    public long TotalErrors { get; set; }
    public decimal Arpu { get; set; }
    public decimal Arppu { get; set; }
    public decimal AvgPurchasePrice { get; set; }
    public int NewUsers { get; set; }
}

public class RollingThirtyDayOverviewReportRecord
{
    public static string GetHeader() =>
        "Timestamp,TotalLogins,UniqueLogins,UniquePayers,Revenue,Purchases,TotalCalls,TotalSuccessfulCalls,TotalErrors,Arpu,Arppu,AvgPurchasePrice,NewUsers";

    public string AsCsvRow() =>
        $"{this.Timestamp:yyyy/MM/dd},{this.TotalLogins},{this.UniqueLogins},{this.UniquePayers},{this.Revenue},{this.Purchases},{this.TotalCalls},{this.TotalSuccessfulCalls},{this.TotalErrors},{this.Arpu},{this.Arppu},{this.AvgPurchasePrice},{this.NewUsers}";

    public static string GetDescription() =>
        """
        The provided CSV table contains daily data for the last 30 days capturing game reports for each day, offering valuable insights into player engagement, financial performance, and the overall gameplay experience.
        This dataset offers a comprehensive view into player behavior, enabling data-driven decisions to enhance gameplay, optimize monetization strategies, and improve overall player satisfaction.
        Through its day-by-day breakdown, it allows for precise analysis of temporal patterns, aiding in understanding player dynamics over different times of the week.
        The report has 30 rows where every row reprsents one the day of the last 30 days.
        Description of Columns:
        - Timestamp: The date of a one-day window when the report was compiled, presented in Coordinated Universal Time (UTC).
        - TotalLogins: The aggregate count of player logins during the specified day, revealing the volume of player interactions.
        - UniqueLogins: The distinct number of players who logged into the game within the same day, indicating individual engagement.
        - UniquePayers: The count of unique players who conducted in-game purchases, reflecting the game's monetization reach.
        - Revenue: The cumulative revenue in dollars generated from in-game purchases throughout the day, demonstrating financial performance.
        - Purchases: The total number of in-game transactions carried out by players in the specified day.
        - TotalCalls: The collective sum of player-initiated interactions, encompassing gameplay actions, API requests, and more..
        - TotalSuccessfulCalls: The count of interactions that succeeded without encountering errors, highlighting player satisfaction.
        - TotalErrors: The overall number of errors encountered during interactions, potential indicators of player experience challenges.
        - Arpu (Average Revenue Per User): The average revenue generated per unique player, calculated as Revenue / UniquePayers.
        - Arppu (Average Revenue Per Paying User): The average revenue generated per player who made purchases, calculated as Revenue / UniquePayers.
        - AvgPurchasePrice: The average price of in-game purchases made by players, calculated as Revenue / Purchases.
        - NewUsers: The count of new players who started engaging with the game during the specified day period.
        """;
    public DateTime Timestamp { get; set; }
    public int TotalLogins { get; set; }
    public int UniqueLogins { get; set; }
    public int UniquePayers { get; set; }
    public decimal Revenue { get; set; }
    public int Purchases { get; set; }
    public long TotalCalls { get; set; }
    public long TotalSuccessfulCalls { get; set; }
    public long TotalErrors { get; set; }
    public decimal Arpu { get; set; }
    public decimal Arppu { get; set; }
    public decimal AvgPurchasePrice { get; set; }
    public int NewUsers { get; set; }
}

public class DailyTopItemsReportRecord
{
    public static string GetHeader() => "ItemName,TotalSales,TotalRevenue";

    public string AsCsvRow() =>
        $"{this.ItemName.Replace("[\"", "").Replace("\"]", "")},{this.TotalSales},{this.TotalRevenue}";

    public static string GetDescription() =>
        """
        This dataset presents a thorough view of sales reports for a single day, capturing vital details about specific product performance and revenue generation.
        Each entry sheds light on sales figures per product, helping decision-makers enhance strategies for growth.
        The dataset is valuable for gauging product popularity, revenue trends, and customer engagement.
        The provided data empowers data-driven decision-making and supports efforts to enhance product offerings and optimize sales strategies for sustained success
        Description of Columns:
        - ItemName: The name of the product, representing a distinct item available for purchase.
        - TotalSales: The cumulative count of sales for the specific item, indicating its popularity and market demand.
        - TotalRevenue: The total monetary value of revenue generated from sales of the item in US dollars.
        """;

    public string ItemName { get; set; }
    public int TotalSales { get; set; }
    public decimal TotalRevenue { get; set; }
}

public class EngagementMetricsRollupReportCSVRecord
{
    public static string GetHeader() => "Date,Region,MonthlyActiveUsers,DailyActiveUsers,NewPlayers,Retention1Day,Retention7Day";

    public string AsCsvRow() =>
        $"{this.ReportDate:yyyy/MM/dd},{this.Region},{this.MonthlyActiveUsers},{this.DailyActiveUsers},{this.NewPlayers},{this.Retention1Day},{this.Retention7Day}";

    public static string GetDescription() =>
        """
        The provided CSV table contains weekly aggregated data related to the user activity and retention for a gaming application.
        This data is broken down by different geographic regions, including France, Greater China, Japan, United Kingdom, United States, Latin America, India, Middle East & Africa, Germany, Canada, Western Europe, Asia Pacific, and Central & Eastern Europe.
        Each row represents a different geographic regions, and the columns contain specific metrics related to user engagement.
        There is a special row for each week with the Region set to 'All', which means this row aggregates data across all the regions for that week
        Below is the description of each field in the table:
        - ReportDate: The date for week for which the data is recorded
        - Region: The geographic region to which the data pertains.Examples include Greater China, France, Japan, United Kingdom, United States, Latin America, India, Middle East & Africa, Germany, Canada, Western Europe, Asia Pacific, and Central & Eastern Europe.
        - MonthlyActiveUsers: The total number of unique users who engaged with the game at least once during the month
        - DailyActiveUsers: The total number of unique users who engaged with the game on that week.
        - NewPlayers: The number of new users who joined and engaged with the game on that week.
        - Retention1Day: The percentage of users who returned to the game on the day after their first engagement.
        - Retention7Day: The percentage of users who returned to the game seven days after their first engagement.
        """;

    public DateTime ReportDate { get; set; }
    public string Platform { get; set; }
    public string Region { get; set; }
    public string Segment { get; set; }
    public long MonthlyActiveUsers { get; set; }
    public long DailyActiveUsers { get; set; }
    public long NewPlayers { get; set; }
    public double FocusAverageDuration { get; set; }
    public double FocusAveragePeriodsPerUser { get; set; }
    public long FocusTotalPeriods { get; set; }
    public double Retention1Day { get; set; }
    public double Retention7Day { get; set; }
    public double Retention14Day { get; set; }
    public double Retention30Day { get; set; }
    public double RevenueDollars { get; set; }
}

public class ThirtyDayRetentionReportRecord
{
    public static string GetHeader() => "CohortDate,CohortSize,DaysLater,TotalRetained,PercentRetained";

    public string AsCsvRow() =>
        $"{this.CohortDate:yyyy/MM/dd},{this.CohortSize},{this.DaysLater},{this.TotalRetained},{this.PercentRetained}";

    public static string GetDescription() =>
        """
        The provided CSV table contains retention report for daily cohorts of players in the last 30 days.
        This retention dataset helps analyze player engagement and the effectiveness of retention strategies by tracking player behavior over time periods.
        It can offer insights into player retention rates, allowing game developers to make informed decisions to improve player engagement and overall game experience.
        Below is the description of each field in the table:
        - CohortDate: The timestamp indicating when the retention data was collected
        - CohortSize: The initial size of the cohort, representing the number of players at the beginning of the retention period.
        - DaysLater: The number of days later at which the retention is being measured.
        - TotalRetained: The total number of players retained in the specified cohort after the specified number of days.
        - PercentRetained: The percentage of players retained in the cohort after the specified number of days.
        """;

    [JsonProperty("Ts")]
    public DateTime CohortDate { get; set; }
    public int CohortSize { get; set; }
    [JsonProperty("PeriodsLater")]
    public int DaysLater { get; set; }
    public int TotalRetained { get; set; }
    public double PercentRetained { get; set; }
}
