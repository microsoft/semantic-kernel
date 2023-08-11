// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
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
