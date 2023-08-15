// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Globalization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Reliability;
using Newtonsoft.Json;
using PlayFabExamples.Common.Configuration;
using PlayFabExamples.Common.Logging;
using PlayFabExamples.Example01_DataQnA.Reports;

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
    public static PlayFabReport[] PlayFabReports = null;

    public static async Task RunAsync()
    {
        CancellationToken cancellationToken = CancellationToken.None;
        string[] questions = new string[]
        {
           // "What is my 2-days retention average? Was my 2-days retention in the last few days was better or worse than that?",
           // "How many players played my game yesterday?",
           // "What is the average number of players I had last week excluding Friday and Monday?",
           // "Is my game doing better in USA or in China?",
           // "If the number of monthly active players in France increases by 30%, what would be the percentage increase to the overall monthly active players?",
            "At which specific times of the day were the highest and lowest numbers of purchases recorded? Please provide the actual sales figures for these particular time slots.",
            "Which three items had the highest total sales and which had the highest revenue generated yesterday?",
        };

        PlannerType[] planners = new[]
        {
            // PlannerType.Stepwise,
            // PlannerType.ChatStepwise,
            PlannerType.SimpleAction
        };

        // We're using volotile memory, so pre-load it with data
        IKernel kernel = await GetKernelAsync(cancellationToken);
        await InitializeKernelMemoryAsync(kernel, TestConfiguration.PlayFab.TitleId, cancellationToken);
        InitializeKernelSkills(kernel);

        foreach (string question in questions)
        {
            foreach (PlannerType planner in planners)
            {
                await Console.Out.WriteLineAsync("--------------------------------------------------------------------------------------------------------------------");
                await Console.Out.WriteLineAsync("Planner: " + planner);
                await Console.Out.WriteLineAsync("Question: " + question);
                await Console.Out.WriteLineAsync("--------------------------------------------------------------------------------------------------------------------");

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
                deploymentName: TestConfiguration.AzureOpenAI.EmbeddingDeploymentName,
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

        return kernel;
    }

    private static void InitializeKernelSkills(IKernel kernel)
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
    }

    private static async Task InitializeKernelMemoryAsync(IKernel kernel, string titleId, CancellationToken cancellationToken)
    {
        if (PlayFabReports == null)
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

            // Report 1 - Daily Overview Report
            PlayFabReportColumn[] dailyOverviewReportColumns = new[]
            {
                new PlayFabReportColumn { Name = "Timestamp", Description = "The date and time of a one-hour window when the report was compiled, presented in Coordinated Universal Time (UTC)." },
                new PlayFabReportColumn { Name = "TotalLogins", Description = "The aggregate count of player logins during the specified hour, revealing the volume of player interactions." },
                new PlayFabReportColumn { Name = "UniqueLogins", Description = "The distinct number of players who logged into the game within the same hour, indicating individual engagement." },
                new PlayFabReportColumn { Name = "UniquePayers", Description = "The count of unique players who conducted in-game purchases, reflecting the game's monetization reach." },
                new PlayFabReportColumn { Name = "Revenue", Description = "The cumulative revenue in dollars generated from in-game purchases throughout the hour, demonstrating financial performance." },
                new PlayFabReportColumn { Name = "Purchases", Description = "The total number of in-game transactions carried out by players in the specified hour." },
                // new PlayFabReportColumn { Name = "TotalCalls", Description = "The collective sum of player-initiated interactions, encompassing gameplay actions, API requests, and more." },
                // new PlayFabReportColumn { Name = "TotalSuccessfulCalls", Description = "The count of interactions that succeeded without encountering errors, highlighting player satisfaction." },
                // new PlayFabReportColumn { Name = "TotalErrors", Description = "The overall number of errors encountered during interactions, potential indicators of player experience challenges." },
                new PlayFabReportColumn { Name = "Arpu", Description = "Average Revenue Per User, The average revenue generated per unique player, calculated as Revenue / UniquePayers." },
                new PlayFabReportColumn { Name = "Arppu", Description = "Average Revenue Per Paying User. The average revenue generated per player who made purchases, calculated as Revenue / UniquePayers." },
                new PlayFabReportColumn { Name = "AvgPurchasePrice", Description = "The average price of in-game purchases made by players, calculated as Revenue / Purchases." },
                new PlayFabReportColumn { Name = "NewUsers", Description = "The count of new players who started engaging with the game during the specified hour period." },
            };

            PlayFabReport dailyOverviewReport = new()
            {
                Columns = dailyOverviewReportColumns,
                Description = "Granular single day data capturing game reports for each hour. The report has 24 rows where every row reprsents one hour of the day.",
                CsvData = PlayFabReport.CreateCsvReportFromJsonArray(latestReports["DailyOverviewReport"].ReportData, dailyOverviewReportColumns),
                ReportName = "DailyOverviewReport"
            };

            // Report 2 - Rolling 30 Day Overview Report
            PlayFabReportColumn[] rollingThirtyDayOverviewReportColumns = new[]
            {
                new PlayFabReportColumn { Name = "Timestamp", Description = "The date and time of a one-hour window when the report was compiled, presented in Coordinated Universal Time (UTC)." },
                new PlayFabReportColumn { Name = "TotalLogins", Description = "The aggregate count of player logins during the specified hour, revealing the volume of player interactions." },
                new PlayFabReportColumn { Name = "UniqueLogins", Description = "The distinct number of players who logged into the game within the same hour, indicating individual engagement." },
                new PlayFabReportColumn { Name = "UniquePayers", Description = "The count of unique players who conducted in-game purchases, reflecting the game's monetization reach." },
                new PlayFabReportColumn { Name = "Revenue", Description = "The cumulative revenue in dollars generated from in-game purchases throughout the hour, demonstrating financial performance." },
                new PlayFabReportColumn { Name = "Purchases", Description = "The total number of in-game transactions carried out by players in the specified hour." },
                // new PlayFabReportColumn { Name = "TotalCalls", Description = "The collective sum of player-initiated interactions, encompassing gameplay actions, API requests, and more." },
                // new PlayFabReportColumn { Name = "TotalSuccessfulCalls", Description = "The count of interactions that succeeded without encountering errors, highlighting player satisfaction." },
                // new PlayFabReportColumn { Name = "TotalErrors", Description = "The overall number of errors encountered during interactions, potential indicators of player experience challenges." },
                new PlayFabReportColumn { Name = "Arpu", Description = "Average Revenue Per User. The average revenue generated per unique player, calculated as Revenue / UniquePayers." },
                new PlayFabReportColumn { Name = "Arppu", Description = "Average Revenue Per Paying User. The average revenue generated per player who made purchases, calculated as Revenue / UniquePayers." },
                new PlayFabReportColumn { Name = "AvgPurchasePrice", Description = "The average price of in-game purchases made by players, calculated as Revenue / Purchases." },
                new PlayFabReportColumn { Name = "NewUsers", Description = "The count of new players who started engaging with the game during the specified hour period." },
            };

            PlayFabReport rollingThirtyDayOverviewReport = new()
            {
                Columns = rollingThirtyDayOverviewReportColumns,
                Description = "Daily data for the last 30 days capturing game reports for each day. The report has 30 rows where every row reprsents one the day of the last 30 days.",
                CsvData = PlayFabReport.CreateCsvReportFromJsonArray(latestReports["RollingThirtyDayOverviewReport"].ReportData, rollingThirtyDayOverviewReportColumns),
                ReportName = "RollingThirtyDayOverviewReport"
            };

            // Report 3 - Daily Top Items Report
            string ParseItemName(string str) => str.Replace("[\"", "").Replace("\"]", "");
            PlayFabReportColumn[] dailyTopItemsReportColumns = new[]
            {
                new PlayFabReportColumn { Name = "ItemName", SourceParser=ParseItemName, Description = "The name of the product, representing a distinct item available for purchase." },
                new PlayFabReportColumn { Name = "TotalSales", Description = "The cumulative count of sales for the specific item, indicating its popularity and market demand." },
                new PlayFabReportColumn { Name = "TotalRevenue", Description = "The total monetary value of revenue generated from sales of the item in US dollars." },
            };

            PlayFabReport dailyTopItemsReport = new()
            {
                Columns = dailyTopItemsReportColumns,
                Description = "The dataset provides an overview of a sales reports, delivering total sales and total revenue, for individual products.",
                CsvData = PlayFabReport.CreateCsvReportFromJsonArray(latestReports["DailyTopItemsReport"].ReportData, dailyTopItemsReportColumns),
                ReportName = "DailyTopItemsReport"
            };

            // Report 4 - Rolling 30 Day Retention Report
            string ParseDailyReportDate(string str) => DateTime.Parse(str, CultureInfo.InvariantCulture).ToString("yyyy/MM/dd", CultureInfo.InvariantCulture);
            PlayFabReportColumn[] thirtyDayRetentionReportColumns = new[]
            {
                new PlayFabReportColumn { Name = "CohortDate", SourceName="Ts", SourceParser=ParseDailyReportDate, Description = "The timestamp indicating when the retention data was collected" },
                new PlayFabReportColumn { Name = "CohortSize", Description = "The initial size of the cohort, representing the number of players at the beginning of the retention period." },
                new PlayFabReportColumn { Name = "DaysLater", SourceName="PeriodsLater", Description = "The number of days later at which the retention is being measured." },
                new PlayFabReportColumn { Name = "TotalRetained", Description = "The total number of players retained in the specified cohort after the specified number of days." },
                new PlayFabReportColumn { Name = "PercentRetained", Description = "The percentage of players retained in the cohort after the specified number of days." },
            };

            PlayFabReport thirtyDayRetentionReport = new()
            {
                Columns = thirtyDayRetentionReportColumns,
                Description = "Retention report for daily cohorts of players in the last 30 days.",
                CsvData = PlayFabReport.CreateCsvReportFromJsonArray(latestReports["ThirtyDayRetentionReport"].ReportData, thirtyDayRetentionReportColumns),
                ReportName = "ThirtyDayRetentionReport"
            };

            // Report 5 - Engagement Mertics Report
            PlayFabReportColumn[] engagementMetricsRollupReportColumns = new[]
            {
                new PlayFabReportColumn { Name = "ReportDate", Description = "The date for the week for which the data is recorded." },
                new PlayFabReportColumn { Name = "Region", Description = "The geographic region to which the data pertains. Examples include Greater China, France, Japan, United Kingdom, United States, Latin America, India, Middle East & Africa, Germany, Canada, Western Europe, Asia Pacific, and Central & Eastern Europe. 'All' is a special region which means this rows aggregates data across all the other regions" },
                new PlayFabReportColumn { Name = "MonthlyActiveUsers", Description = "The total number of unique users who engaged with the game at least once during the month." },
                new PlayFabReportColumn { Name = "DailyActiveUsers", Description = "The total number of unique users who engaged with the game on that week." },
                new PlayFabReportColumn { Name = "NewPlayers", Description = "The number of new users who joined and engaged with the game on that week." },
                new PlayFabReportColumn { Name = "Retention1Day", Description = "The percentage of users who returned to the game on the day after their first engagement." },
                new PlayFabReportColumn { Name = "Retention7Day", Description = "The percentage of users who returned to the game seven days after their first engagement." },
            };

            PlayFabReport engagementMetricsRollupReport = new()
            {
                Columns = engagementMetricsRollupReportColumns,
                Description = """
Weekly aggregated data related to the user activity and retention for the last 30 days.
Data is broken down by different geographic regions, including France, Greater China, Japan, United Kingdom, United States, Latin America, India, Middle East & Africa, Germany, Canada, Western Europe, Asia Pacific, and Central & Eastern Europe.
There is a special row for each week with the Region set to 'All', which means this row aggregates data across all the regions for that week.
""",
                CsvData = string.Join(
                    Environment.NewLine,
                    latestReports["EngagementMetricsRollupReportCSV"].ReportData
                        .Split("\"", StringSplitOptions.RemoveEmptyEntries)
                        .Where(line => line != ",")
                        .Select(line => line.Split(",", StringSplitOptions.RemoveEmptyEntries))
                        .Where(row => row[2] == "All" && row[4] == "All") // Platform and Segment
                        .Select(row => $"{ParseDailyReportDate(row[1])},{row[3]},{row[5]},{row[6]},{row[7]},{row[11]},{row[12]}")
                        .ToList()),
                ReportName = "EngagementMetricsRollupReport"
            };

            PlayFabReports = new[]
            {
                dailyOverviewReport,
                rollingThirtyDayOverviewReport,
                dailyTopItemsReport,
                thirtyDayRetentionReport,
                engagementMetricsRollupReport
            };
        }

        foreach (PlayFabReport report in PlayFabReports)
        {
            string reportText = report.GetDetailedDescription(); // + Environment.NewLine + "Report Data: " + Environment.NewLine + report.GetCsvHeader() + Environment.NewLine + report.CsvData;
            await kernel.Memory.SaveInformationAsync(
                collection: "TitleID-Reports",
                text: reportText,
                id: report.ReportName,
                additionalMetadata: JsonConvert.SerializeObject(report, Formatting.None),
                cancellationToken: cancellationToken);
        }
    }
}
