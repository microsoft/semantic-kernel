// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// Represents the settings used to configure the multi-completion analysis process.
/// </summary>
public class MultiCompletionAnalysisSettings : IDisposable
{
    /// <summary>
    /// Event raised when a new series of Tests were evaluated for validity
    /// </summary>
    public event EventHandler<EvaluationCompletedEventArgs>? EvaluationCompleted;

    /// <summary>
    /// Event raised when new suggested settings were generated from evaluations
    /// </summary>
    public event EventHandler<SuggestionCompletedEventArgs>? SuggestionCompleted;

    /// <summary>
    /// Event raised when the long running analysis task has crashed
    /// </summary>
    public event EventHandler<AnalysisTaskCrashedEventArgs>? AnalysisTaskCrashed;

    /// <summary>
    /// Event raised when a new batch of samples for analysis is received
    /// </summary>
    public event EventHandler<SamplesReceivedEventArgs>? SamplesReceived;

    /// <summary>
    /// Those are the default settings used for connectors evaluation
    /// </summary>
    public static readonly CompleteRequestSettings DefaultVettingRequestSettings = new()
    {
        MaxTokens = 1,
        Temperature = 0.0,
        ResultsPerPrompt = 1,
    };

    private readonly Channel<AnalysisJob> _analysisChannel = Channel.CreateUnbounded<AnalysisJob>();

    // Lock for thread-safe file operations
    private readonly object _analysisFileLock = new();

    // used for manual release of analysis tasks
    private TaskCompletionSource<bool>? _manualTrigger;
    private readonly object _triggerLock = new();
    private readonly CancellationTokenSource _internalCancellationTokenSource = new();

    /// <summary>
    /// Enable or disable the analysis
    /// </summary>
    public bool EnableAnalysis { get; set; } = false;

    /// <summary>
    /// The path to store analysis results
    /// </summary>
    public string AnalysisFilePath { get; set; } = ".\\MultiTextCompletion-analysis.json";

    /// <summary>
    /// Duration before analysis is started when a new event is recorded
    /// </summary>
    public TimeSpan AnalysisDelay { get; set; } = TimeSpan.FromSeconds(1);

    /// <summary>
    /// If true, analysis tasks start normally after the Analysis delay is awaited, but then await for a manual trigger using <see cref="ReleaseAnalysisTasks"/> to proceed and complete
    /// </summary>
    public bool AnalysisAwaitsManualTrigger { get; set; } = false;

    /// <summary>
    /// Enable or disable the analysis
    /// </summary>
    public bool EnableConnectorTests { get; set; } = true;

    /// <summary>
    /// By default, primary completion is tested for duration and cost performances like other secondary connectors. If disabled, primary completion will serve only as the default completion: any validated secondary completion will be preferred.
    /// </summary>
    public bool TestPrimaryCompletion { get; set; } = true;

    /// <summary>
    /// Time period to conduct Tests
    /// </summary>
    public TimeSpan TestsPeriod { get; set; } = TimeSpan.FromSeconds(10);

    /// <summary>
    /// Max number of distinct tests run in parallel
    /// </summary>
    public int MaxDegreeOfParallelismTests { get; set; } = 1;

    /// <summary>
    /// Max number of distinct connectors tested for each test in parallel
    /// </summary>
    public int MaxDegreeOfParallelismConnectorsByTest { get; set; } = 3;

    /// <summary>
    /// In order to better assess model capabilities, one might want to increase temperature just for testing. This might enable the use of fewer prompts
    /// </summary>
    [JsonIgnore]
    public Func<double, double>? TestsTemperatureTransform { get; set; }

    /// <summary>
    /// Enable or disable the evaluation of test prompts
    /// </summary>
    public bool EnableTestEvaluations { get; set; } = true;

    /// <summary>
    /// Time period to conduct evaluations
    /// </summary>
    public TimeSpan EvaluationPeriod { get; set; } = TimeSpan.FromSeconds(10);

    /// <summary>
    /// Max number of evaluations to run in parallel
    /// </summary>
    public int MaxDegreeOfParallelismEvaluations { get; set; } = 5;

    /// <summary>
    /// Determine if self-vetting should be used
    /// </summary>
    public bool UseSelfVetting { get; set; } = false;

    /// <summary>
    /// Enable or disable the suggestion of new settings from evaluation
    /// </summary>
    public bool EnableSuggestion { get; set; } = true;

    /// <summary>
    /// Time period to conduct suggestion analysis
    /// </summary>
    public TimeSpan SuggestionPeriod { get; set; } = TimeSpan.FromMinutes(1);

    /// <summary>
    /// Indicates whether to update suggested settings after analysis
    /// </summary>
    public bool UpdateSuggestedSettings { get; set; } = true;

    /// <summary>
    /// Indicates whether to save suggested settings after analysis
    /// </summary>
    public bool SaveSuggestedSettings { get; set; } = false;

    /// <summary>
    /// Indicates whether to Analysis file with evaluations can be deleted after new suggested settings are saved or applied
    /// </summary>
    public bool DeleteAnalysisFile { get; set; } = true;

    /// <summary>
    ///  Path to save the MultiTextCompletion settings
    /// </summary>
    public string MultiCompletionSettingsFilePath { get; set; } = ".\\MultiTextCompletionSettings.json";

    /// <summary>
    /// Number of prompt tests to be run for each prompt type for each connector to test
    /// </summary>
    public int NbPromptTests { get; set; } = 3;

    /// <summary>
    /// The vetting prompt used in evaluation
    /// </summary>
    public string VettingPromptTemplate { get; set; } = Defaults.VettingPromptTemplate;

    /// <summary>
    /// Request settings for the vetting process
    /// </summary>
    public CompleteRequestSettings VettingRequestSettings { get; set; } = DefaultVettingRequestSettings;

    /// <summary>
    /// Loads the completion analysis file according to settings
    /// </summary>
    public MultiCompletionAnalysis LoadMultiCompletionAnalysis()
    {
        MultiCompletionAnalysis completionAnalysis = new()
        {
            Timestamp = DateTime.MinValue
        };

        if (File.Exists(this.AnalysisFilePath))
        {
            lock (this._analysisFileLock)
            {
                var json = File.ReadAllText(this.AnalysisFilePath);
                completionAnalysis = Json.Deserialize<MultiCompletionAnalysis>(json) ?? completionAnalysis;
            }
        }

        return completionAnalysis;
    }

    /// <summary>
    /// Gets the vetting prompt and vetting request settings to evaluate a given ConnectorTest.
    /// </summary>
    public CompletionJob GetVettingCompletionJob(string prompt, string result)
    {
        var vettingPrompt = this.VettingPromptTemplate.Replace("{prompt}", prompt).Replace("{response}", result);
        var vettingRequestSettings = this.VettingRequestSettings;
        return new CompletionJob(vettingPrompt, vettingRequestSettings);
    }

    private Regex? _vettingCaptureRegex;

    /// <summary>
    /// Accounting for the <see cref="VettingPromptTemplate"/> template, this method uses custom regex to return the prompt and response components of a given vetting prompt.
    /// </summary>
    public (string prompt, string response) CaptureVettingPromptComponents(string vettingPrompt)
    {
        if (this._vettingCaptureRegex == null)
        {
            var vettingPattern = Regex.Escape(this.VettingPromptTemplate)
                                     .Replace(Regex.Escape("{prompt}"), "(?<prompt>[\\s\\S]+?)")
                                     .Replace(Regex.Escape("{response}"), "(?<response>[\\s\\S]+?)")
                                 // Append a pattern to account for the rest of the text
                                 + "[\\s\\S]*";

            // RegexOptions.Singleline makes the '.' special character match any character (including \n)
            this._vettingCaptureRegex = new Regex(vettingPattern, RegexOptions.Singleline);
        }

        var capture = this._vettingCaptureRegex.Match(vettingPrompt);
        return (capture.Groups["prompt"].Value.Trim(), capture.Groups["response"].Value.Trim());
    }

    public bool SaveSamplesNeedRunningTest(List<ConnectorTest> newSamples, AnalysisJob analysisJob)
    {
        // Trigger the EvaluationCompleted event
        if (this.SamplesReceived != null)
        {
            this.SamplesReceived.Invoke(this, new SamplesReceivedEventArgs(newSamples, analysisJob));
            analysisJob.Logger?.LogTrace(message: "SamplesReceived event raised");
        }

        var analysis = new MultiCompletionAnalysis()
        {
            Timestamp = DateTime.MinValue
        };

        var uniqueSamples = newSamples.GroupBy(test => test.Prompt).Select(grouping => grouping.First()).ToList();

        bool UpdateSamplesNeedTesting(List<ConnectorTest>? sampleTests, MultiCompletionAnalysis multiCompletionAnalysis)
        {
            analysisJob.Logger?.LogTrace("Found {0} existing original tests", multiCompletionAnalysis.Samples.Count);
            if (sampleTests != null)
            {
                analysisJob.Logger?.LogTrace("Saving new {0} unique original tests", sampleTests.Count);
                multiCompletionAnalysis.Samples.AddRange(sampleTests);
            }

            var now = DateTime.Now;
            bool needRunningTests = this.EnableConnectorTests
                                    && now - multiCompletionAnalysis.TestTimestamp > this.TestsPeriod;
            if (needRunningTests)
            {
                multiCompletionAnalysis.TestTimestamp = now;
            }

            return needRunningTests;
        }

        analysis = this.LockLoadApplySaveProbeNext(uniqueSamples, analysis, UpdateSamplesNeedTesting, out bool needTest, analysisJob.Logger);

        return needTest;
    }

    /// <summary>
    /// Method to add an analysis job to the analysis pipeline. Starts a long running task if it does not exist
    /// </summary>
    public async Task AddAnalysisJobAsync(AnalysisJob analysisJob)
    {
        if (this.EnableAnalysis)
        {
            if (this._analysisTask == null)
            {
                this._analysisTask = await this.StartAnalysisTask(analysisJob).ConfigureAwait(false);
            }

            this._analysisChannel.Writer.TryWrite(analysisJob);
        }
    }

    /// <summary>
    /// Manually cancels the analysis task if it was started for graceful termination.
    /// </summary>
    public void StopAnalysisTask()
    {
        if (this._analysisTask != null)
        {
            this._internalCancellationTokenSource.Cancel();
            this._analysisTask = null;
        }
    }

    /// <summary>
    /// Method to release the tasks awaiting to run the analysis pipeline.
    /// </summary>
    public void ReleaseAnalysisTasks()
    {
        lock (this._triggerLock)
        {
            this._manualTrigger?.SetResult(true);
            this._manualTrigger = null;
        }
    }

    /// <summary>
    /// Asynchronously loads collected sample tests, run tests on provided connectors, run test evaluations and do settings suggestions.
    /// </summary>
    public async Task RunAnalysisPipelineAsync(AnalysisJob analysisJob, bool? useAwaiter = false)
    {
        if (useAwaiter == true)
        {
            await this.RunAnalysisPipelineWithAwaiterAsync(analysisJob).ConfigureAwait(false);
        }
        else
        {
            await this.RunAnalysisPipelineWithoutAwaiterAsync(analysisJob).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Evaluates a ConnectorTest with the primary connector and returns the evaluation.
    /// </summary>
    public async Task<ConnectorPromptEvaluation?> EvaluateConnectorTestAsync(ConnectorTest connectorTest, AnalysisJob analysisJob)
    {
        analysisJob.Logger?.LogTrace("### Starting evaluating connector test");

        NamedTextCompletion? vettingConnector = null;
        if (this.UseSelfVetting)
        {
            vettingConnector = analysisJob.TextCompletions.FirstOrDefault(c => c.Name == connectorTest.ConnectorName);
        }

        // Use primary connector for vetting by default
        vettingConnector ??= analysisJob.TextCompletions[0];

        var evaluation = await this.EvaluateConnectorTestWithCompletionAsync(vettingConnector, connectorTest, analysisJob).ConfigureAwait(false);
        if (evaluation == null)
        {
            analysisJob.Logger?.LogError("Evaluation could not be performed for connector {0}", connectorTest.ConnectorName);
        }

        analysisJob.Logger?.LogDebug("Evaluated connector {0},\nVetted:{1} from: \nPROMPT_EVALUATED:\n{2}\nRESULT_EVALUATED:{3}",
            evaluation?.Test.ConnectorName,
            evaluation?.IsVetted,
            analysisJob.Settings.GeneratePromptLog(evaluation?.Test.Prompt ?? ""),
            analysisJob.Settings.GeneratePromptLog(evaluation?.Test.Result ?? ""));

        analysisJob.Logger?.LogTrace("### Finished evaluating connector test");

        return evaluation;
    }

    #region Private methods

    private async Task RunAnalysisPipelineWithAwaiterAsync(AnalysisJob analysisJob)
    {
        if (this.AnalysisAwaitsManualTrigger)
        {
            await this.WaitForManualTriggerAsync().ConfigureAwait(false);
        }

        await this.RunAnalysisPipelineWithoutAwaiterAsync(analysisJob).ConfigureAwait(false);
    }

    private async Task RunAnalysisPipelineWithoutAwaiterAsync(AnalysisJob analysisJob)
    {
        MultiCompletionAnalysis completionAnalysis;
        var now = DateTime.Now;
        do
        {
            completionAnalysis = await this.RunAnalysisPipelineOnceAsync(analysisJob).ConfigureAwait(false);
            now = DateTime.Now;
        } while (completionAnalysis.Samples.Count > 0 && now - completionAnalysis.TestTimestamp > this.TestsPeriod
                 || completionAnalysis.Tests.Count > 0 && now - completionAnalysis.EvaluationTimestamp > this.EvaluationPeriod);
    }

    private async Task<MultiCompletionAnalysis> RunAnalysisPipelineOnceAsync(AnalysisJob analysisJob)
    {
        MultiCompletionAnalysis completionAnalysis;

        try
        {
            completionAnalysis = this.LoadMultiCompletionAnalysis();
            completionAnalysis.Timestamp = DateTime.Now;
            List<ConnectorTest>? tests = null;

            // Run new tests

            if (completionAnalysis.Samples.Count > 0)
            {
                tests = await this.RunConnectorTestsAsync(completionAnalysis, analysisJob).ConfigureAwait(false);
            }
            else
            {
                analysisJob.Logger?.LogDebug("Not original test found. No new Test triggered.");
            }

            //Save tests to file

            completionAnalysis = this.SaveConnectorTestsReturnNeedEvaluate(tests, completionAnalysis, analysisJob.Logger, out var needEvaluate);

            // Run evaluations

            List<ConnectorPromptEvaluation>? currentEvaluations = null;

            if (!needEvaluate)
            {
                analysisJob.Logger?.LogDebug("Evaluation cancelled. Nb trailing Original Tests:{0}, Nb trailing Tests:{1}, Elapsed since last Evaluation{2}", completionAnalysis.Samples.Count, completionAnalysis.Tests.Count, DateTime.Now - completionAnalysis.EvaluationTimestamp);
                return completionAnalysis;
            }

            currentEvaluations = await this.RunConnectorTestsEvaluationsAsync(completionAnalysis, analysisJob).ConfigureAwait(false);
            //Save evaluations to file

            completionAnalysis = this.SaveEvaluationsReturnNeedSuggestion(currentEvaluations, completionAnalysis, out var needSuggestion, analysisJob.Logger);

            // Trigger the EvaluationCompleted event
            if (this.EvaluationCompleted != null)
            {
                this.EvaluationCompleted.Invoke(this, new EvaluationCompletedEventArgs(completionAnalysis));
                analysisJob.Logger?.LogTrace(message: "EvaluationCompleted event raised");
            }

            // If update or save suggested settings are enabled, suggest new settings from analysis and save them if needed
            if (!needSuggestion)
            {
                analysisJob.Logger?.LogDebug("Suggestion Cancelled. No new settings suggested. Nb trailing Original Tests:{0}, Nb trailing Tests:{1},  Nb Evaluations:{2} Elapsed since last Suggestion{2}", completionAnalysis.Samples.Count, completionAnalysis.Tests.Count, completionAnalysis.Evaluations.Count, DateTime.Now - completionAnalysis.SuggestionTimestamp);
                return completionAnalysis;
            }

            analysisJob.Logger?.LogTrace("Suggesting new MultiCompletion settings according to evaluation.");
            var updatedSettings = this.ComputeNewSettingsFromAnalysis(analysisJob.TextCompletions, analysisJob.Settings, this.UpdateSuggestedSettings, analysisJob.Logger, analysisJob.CancellationToken);
            if (this.SaveSuggestedSettings)
            {
                // Save the new settings
                string settingsJson = Json.Serialize(updatedSettings.SuggestedSettings);

                File.WriteAllText(this.MultiCompletionSettingsFilePath, settingsJson);
            }

            if (this.DeleteAnalysisFile)
            {
                analysisJob.Logger?.LogTrace("Deleting evaluation file {0}", this.AnalysisFilePath);
                lock (this._analysisFileLock)
                {
                    if (File.Exists(this.AnalysisFilePath))
                    {
                        File.Delete(this.AnalysisFilePath);
                    }
                }
            }

            // Trigger the EvaluationCompleted event
            if (this.SuggestionCompleted != null)
            {
                analysisJob.Logger?.LogTrace(message: "SuggestionCompleted event raised");
                this.SuggestionCompleted.Invoke(this, updatedSettings);
            }
        }
        catch (AIException exception)
        {
            analysisJob.Logger?.LogError("Analysis pipeline failed with AI exception {0}", exception, exception.Detail);
            completionAnalysis = new();
        }
        catch (IOException exception)
        {
            analysisJob.Logger?.LogError("Analysis pipeline failed with IO exception {0}, \nCheck Analysis file path for locks: {1}", exception, exception.Message, this.AnalysisFilePath);
            completionAnalysis = new();
        }
        catch (Exception exception)
        {
            var message = "MultiCompletion analysis pipeline failed";
            analysisJob.Logger?.LogError("{0} with exception {1}", exception, message, exception.Message);
            this.AnalysisTaskCrashed?.Invoke(this, new(new(exception)));
            throw new SKException(message, exception);
        }

        return completionAnalysis;
    }

    private async Task<List<ConnectorTest>> RunConnectorTestsAsync(MultiCompletionAnalysis completionAnalysis, AnalysisJob analysisJob)
    {
        ConcurrentBag<ConnectorTest> tests = new();
        analysisJob.Logger?.LogTrace("## Starting running connector tests from {0} original prompts", completionAnalysis.Samples.Count);

        var tasks = new List<Task>();
        using SemaphoreSlim testSemaphore = new(this.MaxDegreeOfParallelismTests);

        foreach (ConnectorTest sampleTest in completionAnalysis.Samples)
        {
            tasks.Add(Task.Run(async () =>
            {
                await testSemaphore.WaitAsync(analysisJob.CancellationToken).ConfigureAwait(false);
                try
                {
                    string promptLog = analysisJob.Settings.GeneratePromptLog(sampleTest.Prompt);
                    analysisJob.Logger?.LogTrace("Starting running tests for prompt:\n {0} ", promptLog);

                    var testJob = new CompletionJob(sampleTest.Prompt, sampleTest.RequestSettings);
                    var testPromptSettings = analysisJob.Settings.GetPromptSettings(testJob, out var isNew);

                    // Generate tests
                    var connectorsToTest = testPromptSettings.GetCompletionsToTest(sampleTest, analysisJob.TextCompletions, this.TestPrimaryCompletion);

                    using SemaphoreSlim testConnectorsSemaphore = new(this.MaxDegreeOfParallelismConnectorsByTest);

                    var subTasks = new List<Task>();

                    foreach (var namedTextCompletion in connectorsToTest)
                    {
                        subTasks.Add(Task.Run(async () =>
                        {
                            await testConnectorsSemaphore.WaitAsync(analysisJob.CancellationToken).ConfigureAwait(false);
                            try
                            {
                                await this.RunTestForConnectorAsync(namedTextCompletion, testJob, testPromptSettings, tests, analysisJob).ConfigureAwait(false);
                            }
                            finally
                            {
                                testConnectorsSemaphore.Release();
                            }
                        }, analysisJob.CancellationToken));
                    }

                    await Task.WhenAll(subTasks).ConfigureAwait(false);
                }
                finally
                {
                    testSemaphore.Release();
                }
            }, analysisJob.CancellationToken));
        }

        await Task.WhenAll(tasks).ConfigureAwait(false);

        analysisJob.Logger?.LogTrace("## Finished running connector tests returning {0} tests to evaluate", tests.Count);

        return tests.ToList();
    }

    private async Task RunTestForConnectorAsync(NamedTextCompletion namedTextCompletion, CompletionJob testJob, PromptMultiConnectorSettings promptMultiConnectorSettings, ConcurrentBag<ConnectorTest> connectorTests, AnalysisJob analysisJob)
    {
        analysisJob.Logger?.LogTrace("### Running Tests for connector {0}, {1} tests per prompt configured", namedTextCompletion.Name, this.NbPromptTests);

        var tasks = new List<Task>();
        using SemaphoreSlim testSemaphore = new(namedTextCompletion.MaxDegreeOfParallelism);

        for (int i = 0; i < this.NbPromptTests; i++)
        {
            tasks.Add(Task.Run(async () =>
            {
                await testSemaphore.WaitAsync(analysisJob.CancellationToken).ConfigureAwait(false);
                try
                {
                    var stopWatch = Stopwatch.StartNew();
                    var promptConnectorSettings = promptMultiConnectorSettings.GetConnectorSettings(namedTextCompletion.Name);

                    var session = new MultiCompletionSession(testJob,
                        promptMultiConnectorSettings,
                        false,
                        namedTextCompletion,
                        analysisJob.TextCompletions,
                        promptConnectorSettings,
                        analysisJob.Settings,
                        analysisJob.Logger);

                    session.AdjustPromptAndRequestSettings();
                    if (this.TestsTemperatureTransform != null)
                    {
                        var temperatureUpdater = new SettingsUpdater<CompleteRequestSettings>(session.CallJob.RequestSettings, MultiTextCompletionSettings.CloneRequestSettings);
                        var adjustedSettings = temperatureUpdater.ModifyIfChanged(settings => settings.Temperature, this.TestsTemperatureTransform, (settings, newTemp) => settings.Temperature = newTemp, out var settingChanged);
                        if (settingChanged)
                        {
                            session.CallJob = new CompletionJob(session.CallJob.Prompt, adjustedSettings);
                        }
                    }

                    var completions = await namedTextCompletion.TextCompletion.GetCompletionsAsync(session.CallJob.Prompt, session.CallJob.RequestSettings, analysisJob.CancellationToken).ConfigureAwait(false);

                    var firstResult = completions[0];
                    string result = await firstResult.GetCompletionAsync(analysisJob.CancellationToken).ConfigureAwait(false) ?? string.Empty;

                    stopWatch.Stop();
                    var duration = stopWatch.Elapsed;
                    decimal textCompletionCost = namedTextCompletion.GetCost(session.CallJob.Prompt, result);

                    // For the evaluation task. We don't keep the adjusted settings since prompt type matching is based on the original prompt
                    var connectorTest = ConnectorTest.Create(testJob, namedTextCompletion, result, duration, textCompletionCost);
                    connectorTests.Add(connectorTest);

                    analysisJob.Logger?.LogDebug("Generated Test results for connector {0}, temperature: {1} duration: {2}\nTEST_PROMPT:\n{3}\nTEST_RESULT:\n{4} ", connectorTest.ConnectorName, session.CallJob.RequestSettings.Temperature, connectorTest.Duration, analysisJob.Settings.GeneratePromptLog(session.CallJob.Prompt), analysisJob.Settings.GeneratePromptLog(connectorTest.Result));
                }
                catch (AIException exception)
                {
                    analysisJob.Logger?.LogError(exception, "Failed to run test prompt with connector {2}\nException:{0}Prompt:\n{1} ", exception, exception.ToString(), testJob.Prompt, namedTextCompletion.Name);
                }
                finally
                {
                    testSemaphore.Release();
                }
            }, analysisJob.CancellationToken));
        }

        await Task.WhenAll(tasks).ConfigureAwait(false);

        analysisJob.Logger?.LogTrace("### Finished Running Tests for connector {0}, {1} tests were run", namedTextCompletion.Name, this.NbPromptTests);
    }

    private MultiCompletionAnalysis SaveConnectorTestsReturnNeedEvaluate(List<ConnectorTest>? newTests, MultiCompletionAnalysis analysis, ILogger? logger, out bool needEvaluate)
    {
        bool UpdateTestsAndProbeEvaluate(List<ConnectorTest>? tests, MultiCompletionAnalysis multiCompletionAnalysis)
        {
            if (tests != null)
            {
                var originalTestPromptsToRemove = tests.Select(test => test.Prompt).Distinct();
                multiCompletionAnalysis.Samples.RemoveAll(test => originalTestPromptsToRemove.Contains(test.Prompt));
            }

            logger?.LogTrace("Found {0} existing tests", multiCompletionAnalysis.Tests.Count);
            if (tests != null)
            {
                logger?.LogTrace("Saving new {0} tests", tests.Count);
                multiCompletionAnalysis.Tests.AddRange(tests);
            }

            var now = DateTime.Now;
            bool needEvaluate = this.EnableTestEvaluations
                                && multiCompletionAnalysis.Tests.Count > 0
                                && now - multiCompletionAnalysis.EvaluationTimestamp > this.EvaluationPeriod
                                && multiCompletionAnalysis.Samples.Count == 0
                                || now - multiCompletionAnalysis.TestTimestamp < this.TestsPeriod;
            if (needEvaluate)
            {
                multiCompletionAnalysis.EvaluationTimestamp = now;
            }

            return needEvaluate;
        }

        return this.LockLoadApplySaveProbeNext(newTests, analysis, UpdateTestsAndProbeEvaluate, out needEvaluate, logger);
    }

    private async Task<List<ConnectorPromptEvaluation>> RunConnectorTestsEvaluationsAsync(MultiCompletionAnalysis completionAnalysis, AnalysisJob analysisJob)
    {
        var currentEvaluations = new ConcurrentBag<ConnectorPromptEvaluation>();
        analysisJob.Logger?.LogTrace("## Generating Evaluations from prompt test results");

        var tasks = new List<Task>();
        var maxDegreeParallelism = Math.Min(this.MaxDegreeOfParallelismEvaluations, completionAnalysis.Tests.Count);
        using SemaphoreSlim evaluationSemaphore = new(this.MaxDegreeOfParallelismEvaluations);

        foreach (var connectorTest in completionAnalysis.Tests)
        {
            tasks.Add(Task.Run(async () =>
            {
                await evaluationSemaphore.WaitAsync(analysisJob.CancellationToken).ConfigureAwait(false);
                try
                {
                    var evaluation = await this.EvaluateConnectorTestAsync(connectorTest, analysisJob).ConfigureAwait(false);
                    if (evaluation != null)
                    {
                        currentEvaluations.Add(evaluation);
                    }
                }
                finally
                {
                    evaluationSemaphore.Release();
                }
            }, analysisJob.CancellationToken));
        }

        await Task.WhenAll(tasks).ConfigureAwait(false);

        analysisJob.Logger?.LogTrace("## Finished Generating Evaluations from prompt test results");

        return currentEvaluations.ToList();
    }

    private async Task<ConnectorPromptEvaluation?> EvaluateConnectorTestWithCompletionAsync(NamedTextCompletion vettingCompletion, ConnectorTest connectorTest, AnalysisJob analysisJob)
    {
        var prompt = this.VettingPromptTemplate.Replace("{prompt}", connectorTest.Prompt).Replace("{response}", connectorTest.Result);

        var vettingJob = new CompletionJob(prompt, this.VettingRequestSettings);
        var vettingPromptSettings = analysisJob.Settings.GetPromptSettings(vettingJob, out _);
        var vettingPromptConnectorSettings = vettingPromptSettings.GetConnectorSettings(vettingCompletion.Name);

        var session = new MultiCompletionSession(vettingJob,
            vettingPromptSettings,
            false,
            vettingCompletion,
            analysisJob.TextCompletions,
            vettingPromptConnectorSettings,
            analysisJob.Settings,
            analysisJob.Logger);

        session.AdjustPromptAndRequestSettings();
        string completionResult;
        var stopWatch = Stopwatch.StartNew();
        try
        {
            completionResult = await vettingCompletion.TextCompletion.CompleteAsync(prompt, this.VettingRequestSettings, analysisJob.CancellationToken).ConfigureAwait(false) ?? "false";
            stopWatch.Stop();
        }
        catch (AIException exception)
        {
            analysisJob.Logger?.LogError(exception, "Failed to evaluate test prompt with vetting connector {2}\nException:{0}\nVetting Prompt:\n{1} ", exception, exception.ToString(), prompt, vettingCompletion.Name);
            return null;
        }

        var elapsed = stopWatch.Elapsed;

        bool isVetted;
        if (completionResult.Equals("true", StringComparison.OrdinalIgnoreCase))
        {
            isVetted = true;
        }
        else if (completionResult.Equals("false", StringComparison.OrdinalIgnoreCase))
        {
            isVetted = false;
        }
        else
        {
            analysisJob.Logger?.LogError("Failed to evaluate test prompt with vetting connector {2}\nVetting Prompt:\n{1} ", completionResult, prompt, vettingCompletion.Name);
            isVetted = false;
        }

        var toReturn = new ConnectorPromptEvaluation
        {
            Test = connectorTest,
            VettingConnector = vettingCompletion.Name,
            Duration = elapsed,
            IsVetted = isVetted,
        };
        return toReturn;
    }

    private MultiCompletionAnalysis SaveEvaluationsReturnNeedSuggestion(List<ConnectorPromptEvaluation>? newEvaluations, MultiCompletionAnalysis completionAnalysis, out bool needSuggestion, ILogger? logger)
    {
        bool UpdateEvaluationsAndProbeSuggestion(List<ConnectorPromptEvaluation>? evaluations, MultiCompletionAnalysis multiCompletionAnalysis)
        {
            if (evaluations != null)
            {
                var testTimestampsToRemove = evaluations.Select(evaluation => evaluation.Test.Timestamp);
                multiCompletionAnalysis.Tests.RemoveAll(test => testTimestampsToRemove.Contains(test.Timestamp));
            }

            logger?.LogTrace("Found {0} existing evaluations", multiCompletionAnalysis.Evaluations.Count);
            if (evaluations != null)
            {
                logger?.LogTrace("Saving new {0} evaluations", evaluations.Count);
                multiCompletionAnalysis.Evaluations.AddRange(evaluations);
            }

            var now = DateTime.Now;
            bool needSuggestion = this.EnableSuggestion
                                  && (this.UpdateSuggestedSettings || this.SaveSuggestedSettings)
                                  && multiCompletionAnalysis.Evaluations.Count > 0
                                  && now - multiCompletionAnalysis.SuggestionTimestamp > this.SuggestionPeriod
                                  && multiCompletionAnalysis.Tests.Count == 0
                                  || now - multiCompletionAnalysis.EvaluationTimestamp < this.EvaluationPeriod
                                  && multiCompletionAnalysis.Samples.Count == 0
                                  || now - multiCompletionAnalysis.TestTimestamp < this.TestsPeriod;
            if (needSuggestion)
            {
                multiCompletionAnalysis.SuggestionTimestamp = now;
            }

            return needSuggestion;
        }

        return this.LockLoadApplySaveProbeNext(newEvaluations, completionAnalysis, UpdateEvaluationsAndProbeSuggestion, out needSuggestion, logger);
    }

    /// <summary>
    /// Computes new MultiTextCompletionSettings with prompt connector settings based on analysis of their evaluation .
    /// </summary>
    private SuggestionCompletedEventArgs ComputeNewSettingsFromAnalysis(IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, bool updateSettings, ILogger? logger, CancellationToken? cancellationToken = default)
    {
        // If not updating settings in-place, create a new instance
        var settingsToReturn = settings;
        if (!updateSettings)
        {
            settingsToReturn = Json.Deserialize<MultiTextCompletionSettings>(JsonSerializer.Serialize(settings))!;
        }

        MultiCompletionAnalysis completionAnalysis = new();
        // Load evaluation results
        lock (this._analysisFileLock)
        {
            if (File.Exists(this.AnalysisFilePath))
            {
                var json = File.ReadAllText(this.AnalysisFilePath);
                completionAnalysis = Json.Deserialize<MultiCompletionAnalysis>(json) ?? new MultiCompletionAnalysis();
            }
        }

        var evaluationsByPromptSettings = new Dictionary<PromptMultiConnectorSettings, List<ConnectorPromptEvaluation>>();
        foreach (var evaluation in completionAnalysis.Evaluations)
        {
            var evaluationTestCompletionJob = new CompletionJob(evaluation.Test.Prompt, evaluation.Test.RequestSettings);
            var promptSettings = settingsToReturn!.GetPromptSettings(evaluationTestCompletionJob, out _);
            if (promptSettings.PromptType.Instances.Count < settings.MaxInstanceNb && !promptSettings.PromptType.Instances.Contains(evaluation.Test.Prompt))
            {
                promptSettings.PromptType.Instances.Add(evaluation.Test.Prompt);
            }

            if (!evaluationsByPromptSettings.TryGetValue(promptSettings, out List<ConnectorPromptEvaluation>? promptEvaluations))
            {
                promptEvaluations = new List<ConnectorPromptEvaluation>();
                evaluationsByPromptSettings[promptSettings] = promptEvaluations;
            }

            promptEvaluations.Add(evaluation);
        }

        foreach (var promptEvaluations in evaluationsByPromptSettings)
        {
            PromptMultiConnectorSettings promptMultiConnectorSettings = promptEvaluations.Key;
            var evaluationsByConnector = promptEvaluations.Value.GroupBy(e => e.Test.ConnectorName);
            foreach (var connectorEvaluations in evaluationsByConnector)
            {
                var connectorName = connectorEvaluations.Key;

                var promptConnectorSettings = promptMultiConnectorSettings.GetConnectorSettings(connectorName);

                //promptConnectorSettings.Evaluations = connectorEvaluations.ToList();
                promptConnectorSettings.AverageDuration = TimeSpan.FromMilliseconds(connectorEvaluations.Average(e => e.Test.Duration.TotalMilliseconds));
                promptConnectorSettings.AverageCost = connectorEvaluations.Average(e => e.Test.Cost);
                var evaluationsByMainConnector = connectorEvaluations.GroupBy(e => e.VettingConnector).OrderByDescending(grouping => grouping.Count()).First();
                promptConnectorSettings.VettingConnector = evaluationsByMainConnector.Key;
                // We first assess whether the connector is vetted by enough tests
                if (evaluationsByMainConnector.Count() >= settings.AnalysisSettings.NbPromptTests)
                {
                    var vetted = evaluationsByMainConnector.All(e => e.IsVetted);
                    // We then assess whether the connector is vetted by enough varied tests
                    var vettedVaried = evaluationsByMainConnector.Count() > 1 && !evaluationsByMainConnector.GroupBy(evaluation => evaluation.Test.Prompt).Any(grouping => grouping.Count() > 1);
                    promptConnectorSettings.VettingLevel = vetted ? vettedVaried ? VettingLevel.OracleVaried : VettingLevel.Oracle : VettingLevel.Invalid;
                    logger?.LogDebug("Connector  {0}, configured according to evaluations with level:\n{1} for \nPrompt type with signature:\n{2}", connectorName, promptConnectorSettings.VettingLevel, promptMultiConnectorSettings.PromptType.Signature.PromptStart);
                }
            }
        }

        return new SuggestionCompletedEventArgs(completionAnalysis, settingsToReturn);
    }

    private MultiCompletionAnalysis LockLoadApplySaveProbeNext<TEvent>(List<TEvent>? itemsToSave, MultiCompletionAnalysis analysis, Func<List<TEvent>?, MultiCompletionAnalysis, bool> updateAndProbeTimespan, out bool runNextStep, ILogger? logger)
    {
        var currentAnalysis = analysis;

        if (itemsToSave != null)
        {
            lock (this._analysisFileLock)
            {
                if (File.Exists(this.AnalysisFilePath))
                {
                    logger?.LogTrace("Loading Analysis file from {0} to save {1} new instances of {2}", this.AnalysisFilePath, itemsToSave.Count, typeof(TEvent).Name);
                    var json = File.ReadAllText(this.AnalysisFilePath);
                    currentAnalysis = Json.Deserialize<MultiCompletionAnalysis>(json) ?? currentAnalysis;
                }
            }
        }

        runNextStep = updateAndProbeTimespan(itemsToSave, currentAnalysis);

        if (itemsToSave != null || runNextStep)
        {
            lock (this._analysisFileLock)
            {
                var now = DateTime.Now;
                currentAnalysis.Duration = currentAnalysis.Duration.Add(now - currentAnalysis.Timestamp);
                currentAnalysis.Timestamp = DateTime.Now;
                var jsonString = Json.Serialize(currentAnalysis);
                File.WriteAllText(this.AnalysisFilePath, jsonString);
                logger?.LogTrace("Saved existing and new instances of  {0} to {1}", typeof(TEvent).Name, this.AnalysisFilePath);
            }
        }

        return currentAnalysis;
    }

    private Task<bool> WaitForManualTriggerAsync()
    {
        lock (this._triggerLock)
        {
            if (this._manualTrigger == null)
            {
                this._manualTrigger = new TaskCompletionSource<bool>();
            }

            return this._manualTrigger.Task;
        }
    }

    private async Task AnalyzeDataAsync(AnalysisJob initialJob)
    {
        AnalysisJob currentAnalysisJob = initialJob;
        try
        {
            while (await this._analysisChannel.Reader.WaitToReadAsync(currentAnalysisJob.CancellationToken).ConfigureAwait(false))
            {
                while (this._analysisChannel.Reader.TryRead(out var newAnalysisJob))
                {
                    currentAnalysisJob = newAnalysisJob;
                    if (!currentAnalysisJob.CancellationToken.IsCancellationRequested)
                    {
                        var now = DateTime.Now;
                        currentAnalysisJob.Logger?.LogTrace(message: "AnalyzeDataAsync triggered by test batch. Sent: {0}, Received: {1} ", currentAnalysisJob.Timestamp, now);

                        var delay = currentAnalysisJob.Timestamp + this.AnalysisDelay - now;

                        if (delay > TimeSpan.FromMilliseconds(1))
                        {
                            currentAnalysisJob.Logger?.LogTrace(message: "AnalyzeDataAsync adding startup delay {0}", delay);
                            await Task.Delay(delay, currentAnalysisJob.CancellationToken).ConfigureAwait(false);
                        }
                    }
                }

                currentAnalysisJob.Logger?.LogTrace(message: "## AnalyzeDataAsync launches new test and analysis pipeline");
                // Evaluate the test

                await this.RunAnalysisPipelineAsync(currentAnalysisJob, this.AnalysisAwaitsManualTrigger).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException exception)
        {
            if (exception.CancellationToken.Equals(this._internalCancellationTokenSource.Token))
            {
                currentAnalysisJob.Logger?.LogTrace("AnalyzeDataAsync task was Stopped manually");
            }
            else
            {
                currentAnalysisJob.Logger?.LogTrace("AnalyzeDataAsync task was cancelled with exception {0}", exception, exception.ToString());
            }
        }
        catch (Exception exception)
        {
            var message = "AnalyzeDataAsync task failed";
            currentAnalysisJob.Logger?.LogError("{0} with exception {1}", exception, message, exception.ToString());
            throw new SKException(message, exception);
        }
        finally
        {
            this._analysisTask = null;
        }
    }

    private Task? _analysisTask;

    /// <summary>
    /// Starts a management task charged with collecting and analyzing prompt connector usage.
    /// </summary>
    private Task<Task> StartAnalysisTask(AnalysisJob initialJob)
    {
        return Task.Factory.StartNew(
            async () =>
            {
                initialJob.Logger?.LogTrace("# Analysis task was started");

                using (CancellationTokenSource linkedCts =
                       CancellationTokenSource.CreateLinkedTokenSource(initialJob.CancellationToken, this._internalCancellationTokenSource.Token))
                {
                    while (!linkedCts.IsCancellationRequested)
                    {
                        await this.AnalyzeDataAsync(initialJob).ConfigureAwait(false);
                    }
                }

                initialJob.Logger?.LogTrace("# Analysis task was cancelled and is closing gracefully");
            },
            initialJob.CancellationToken,
            TaskCreationOptions.LongRunning,
            TaskScheduler.Default);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    private bool _disposedValue;

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._internalCancellationTokenSource.Dispose();
            }

            this._disposedValue = true;
        }
    }

    #endregion
}
