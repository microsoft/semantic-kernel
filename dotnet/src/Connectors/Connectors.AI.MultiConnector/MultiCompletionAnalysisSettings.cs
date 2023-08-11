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
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the settings used to configure the multi-completion analysis process.
/// </summary>
public class MultiCompletionAnalysisSettings
{
    public event EventHandler<EvaluationCompletedEventArgs>? EvaluationCompleted;
    public event EventHandler<SuggestionCompletedEventArgs>? SuggestionCompleted;

    /// <summary>
    /// This is the default vetting prompt used for connectors evaluation
    /// </summary>
    public const string DefaultVettingPromptTemplate = @"Following are an LLM prompt and the corresponding response from an LLM model to be evaluated. Please indicate whether the response is valid or not. Answer with true or false.
PROMPT:
-------
{prompt}
RESPONSE:
---------
{response}
RESPONSE IS VALID? (true/false):
--------------------------------
";

    /// <summary>
    /// Those are the default settings used for connectors evaluation
    /// </summary>
    public static readonly CompleteRequestSettings DefaultVettingRequestSettings = new()
    {
        MaxTokens = 1,
        Temperature = 0.0,
        ResultsPerPrompt = 1,
    };

    // Lock for thread-safe file operations
    private object _analysisFileLock = new();

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
    /// Enable or disable the analysis
    /// </summary>
    public bool EnableConnectorTests { get; set; } = true;

    /// <summary>
    /// Time period to conduct Tests
    /// </summary>
    public TimeSpan TestsPeriod { get; set; } = TimeSpan.FromSeconds(10);

    /// <summary>
    /// Max number of connectors to test in parallel
    /// </summary>
    public int MaxDegreeOfParallelismConnectorTests { get; set; } = 3;

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
    public bool SaveSuggestedSettings { get; set; } = true;

    /// <summary>
    /// Indicates whether to Analysis file with evaluations can be deleted after new suggested settings are saved or applied
    /// </summary>
    public bool DeleteAnalysisFile { get; set; } = true;

    /// <summary>
    ///  Path to save the MultiTextCompletion settings
    /// </summary>
    public string MultiCompletionSettingsFilePath { get; set; } = ".\\MultiTextCompletionSettings.json";

    /// <summary>
    /// The number of sample to collect for each prompt type
    /// </summary>
    public int MaxInstanceNb { get; set; } = 10;

    /// <summary>
    /// Number of prompt tests to be run for each prompt type for each connector to test
    /// </summary>
    public int NbPromptTests { get; set; } = 3;

    /// <summary>
    /// The vetting prompt used in evaluation
    /// </summary>
    public string VettingPromptTemplate { get; set; } = DefaultVettingPromptTemplate;

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
                completionAnalysis = JsonSerializer.Deserialize<MultiCompletionAnalysis>(json) ?? completionAnalysis;
            }
        }

        return completionAnalysis;
    }

    /// <summary>
    /// Evaluates a ConnectorTest with a NamedTextCompletion instance and returns the evaluation.
    /// </summary>
    public async Task<ConnectorPromptEvaluation?> EvaluateConnectorTestWithCompletionAsync(NamedTextCompletion vettingCompletion, ConnectorTest connectorTest, MultiTextCompletionSettings settings, ILogger? logger, CancellationToken cancellationToken = default)
    {
        var prompt = this.VettingPromptTemplate.Replace("{prompt}", connectorTest.Prompt).Replace("{response}", connectorTest.Result);
        var stopWatch = Stopwatch.StartNew();
        var vettingPromptSettings = settings.GetPromptSettings(prompt, this.VettingRequestSettings, out _);
        var newRequestSettings = vettingCompletion.AdjustPromptAndRequestSettings(prompt, this.VettingRequestSettings, vettingPromptSettings, settings, logger);
        string completionResult;
        try
        {
            completionResult = await vettingCompletion.TextCompletion.CompleteAsync(prompt, this.VettingRequestSettings, cancellationToken).ConfigureAwait(false) ?? "false";
            stopWatch.Stop();
        }
        catch (AIException exception)
        {
            logger?.LogError(exception, "Failed to evaluate test prompt with vetting connector {2}\nException:{0}\nVetting Prompt:\n{1} ", exception, exception.ToString(), prompt, vettingCompletion.Name);
            return null;
        }

        var elapsed = stopWatch.Elapsed;
        var isVetted = completionResult.Equals("true", StringComparison.OrdinalIgnoreCase);
        var toReturn = new ConnectorPromptEvaluation
        {
            Test = connectorTest,
            VettingConnector = vettingCompletion.Name,
            Duration = elapsed,
            IsVetted = isVetted,
        };
        return toReturn;
    }

    /// <summary>
    /// Gets the vetting prompt and vetting request settings to evaluate a given ConnectorTest.
    /// </summary>
    public (string vettingPrompt, CompleteRequestSettings vettingRequestSettings) GetVettingPrompt(string prompt, string result)
    {
        var vettingPrompt = this.VettingPromptTemplate.Replace("{prompt}", prompt).Replace("{response}", result);
        var vettingRequestSettings = this.VettingRequestSettings;
        return (vettingPrompt, vettingRequestSettings);
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

    public bool SaveOriginalTestsReturnNeedRunningTest(List<ConnectorTest> originalTests, ILogger? logger)
    {
        var analysis = new MultiCompletionAnalysis()
        {
            Timestamp = DateTime.MinValue
        };

        bool UpdateOriginalTestsAndProbeTests(MultiCompletionAnalysis multiCompletionAnalysis)
        {
            logger?.LogTrace("Found {0} original tests", multiCompletionAnalysis.OriginalTests.Count);
            var uniqueOriginalTests = originalTests.GroupBy(test => test.Prompt).Select(grouping => grouping.First());
            multiCompletionAnalysis.OriginalTests.AddRange(originalTests);
            bool needRunningTests = (this.EnableConnectorTests)
                                    && (DateTime.Now - multiCompletionAnalysis.TestTimestamp) > this.TestsPeriod;
            if (needRunningTests)
            {
                multiCompletionAnalysis.TestTimestamp = DateTime.Now;
            }

            return needRunningTests;
        }

        logger?.LogTrace("Loading Analysis file from {0} to update original tests", this.AnalysisFilePath);

        analysis = this.LockLoadApplySaveProbeNext(analysis, UpdateOriginalTestsAndProbeTests, out bool needTest, logger);

        logger?.LogTrace("Saved {0} original tests to {1}", originalTests.Count, this.AnalysisFilePath);

        return needTest;
    }

    /// <summary>
    /// Asynchronously evaluates a connector test, writes the evaluation to a file, and updates settings if necessary.
    /// </summary>
    public async Task EvaluatePromptConnectorsAsync(IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, ILogger? logger = null, CancellationToken cancellationToken = default)
    {
        MultiCompletionAnalysis completionAnalysis;

        do
        {
            completionAnalysis = await this.RunAnalysisPipelineAsync(namedTextCompletions, settings, logger, cancellationToken).ConfigureAwait(false);
        } while (completionAnalysis.OriginalTests.Count > 0);
    }

    #region Private methods

    private async Task<MultiCompletionAnalysis> RunAnalysisPipelineAsync(IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, ILogger? logger, CancellationToken cancellationToken)
    {
        MultiCompletionAnalysis completionAnalysis = this.LoadMultiCompletionAnalysis();

        List<ConnectorTest>? tests = null;

        if (completionAnalysis.OriginalTests.Count > 0)
        {
            tests = await this.RunConnectorTestsAsync(completionAnalysis.OriginalTests, namedTextCompletions, settings, logger, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            logger?.LogDebug("Not original test found. No new Test triggered.");
        }

        if (tests == null)
        {
            return completionAnalysis;
        }

        completionAnalysis = this.SaveConnectorTestsReturnNeedEvaluate(tests, completionAnalysis, logger, out var needEvaluate);

        // Generate evaluations

        List<ConnectorPromptEvaluation>? currentEvaluations = null;

        if (needEvaluate)
        {
            currentEvaluations = await this.RunConnectorTestsEvaluationsAsync(tests, namedTextCompletions, settings, logger, cancellationToken).ConfigureAwait(false);
        }
        else
        {
            logger?.LogDebug("Evaluation period not reached. No new Evaluation triggered.");
        }

        if (currentEvaluations == null)
        {
            return completionAnalysis;
        }

        //Save evaluations to file

        completionAnalysis = this.SaveEvaluationsReturnNeedSuggestion(currentEvaluations, completionAnalysis, out var needSuggestion, logger);

        // Trigger the EvaluationCompleted event
        this.EvaluationCompleted?.Invoke(this, new EvaluationCompletedEventArgs(completionAnalysis));
        logger?.LogTrace(message: "EvaluationCompleted event raised");

        // If update or save suggested settings are enabled, suggest new settings from analysis and save them if needed
        if (needSuggestion)
        {
            logger?.LogDebug("Analysis period reached. New settings suggested.");
            var updatedSettings = this.ComputeNewSettingsFromAnalysis(namedTextCompletions, settings, this.UpdateSuggestedSettings, logger, cancellationToken);
            if (this.SaveSuggestedSettings)
            {
                // Save the new settings
                var settingsJson = JsonSerializer.Serialize(updatedSettings, new JsonSerializerOptions() { WriteIndented = true });
                File.WriteAllText(this.MultiCompletionSettingsFilePath, settingsJson);
            }

            if (this.DeleteAnalysisFile)
            {
                logger?.LogTrace("Deleting evaluation file {0}", this.AnalysisFilePath);
                lock (this._analysisFileLock)
                {
                    if (File.Exists(this.AnalysisFilePath))
                    {
                        File.Delete(this.AnalysisFilePath);
                    }
                }
            }

            // Trigger the EvaluationCompleted event
            this.SuggestionCompleted?.Invoke(this, updatedSettings);
            logger?.LogTrace(message: "SuggestionCompleted event raised");
        }
        else
        {
            logger?.LogDebug("Suggestion period not reached. No new settings suggested.");
        }

        return completionAnalysis;
    }

    private async Task<List<ConnectorTest>> RunConnectorTestsAsync(List<ConnectorTest> originalTests, IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, ILogger? logger, CancellationToken cancellationToken)
    {
        ConcurrentBag<ConnectorTest> tests = new();
        logger?.LogTrace("Starting running connector tests from {0} original prompts", originalTests.Count);

        var tasks = new List<Task>();
        using SemaphoreSlim semaphore = new(this.MaxDegreeOfParallelismConnectorTests);

        foreach (ConnectorTest originalTest in originalTests)
        {
            logger?.LogTrace("Starting running tests for prompt:\n {0} ", originalTest.Prompt);

            var promptSettings = settings.GetPromptSettings(originalTest.Prompt, originalTest.RequestSettings, out var isNew);

            // Generate tests
            var connectorsToTest = promptSettings.GetCompletionsToTest(originalTest, namedTextCompletions);

            foreach (var namedTextCompletion in connectorsToTest)
            {
                tasks.Add(Task.Run(async () =>
                {
                    await semaphore.WaitAsync(cancellationToken).ConfigureAwait(false);
                    try
                    {
                        await this.RunTestForConnectorAsync(namedTextCompletion, originalTest, settings, tests, logger, cancellationToken).ConfigureAwait(false);
                    }
                    finally
                    {
                        semaphore.Release();
                    }
                }, cancellationToken));
            }
        }

        await Task.WhenAll(tasks).ConfigureAwait(false);

        return tests.ToList();
    }

    private async Task RunTestForConnectorAsync(NamedTextCompletion namedTextCompletion, ConnectorTest originalTest, MultiTextCompletionSettings multiTextCompletionSettings, ConcurrentBag<ConnectorTest> tests, ILogger? logger, CancellationToken cancellationToken)
    {
        logger?.LogTrace("Running Tests for connector {0} ", namedTextCompletion.Name);

        for (int i = 0; i < this.NbPromptTests; i++)
        {
            var stopWatch = Stopwatch.StartNew();
            try
            {
                PromptMultiConnectorSettings promptMultiConnectorSettings = multiTextCompletionSettings.GetPromptSettings(originalTest.Prompt, originalTest.RequestSettings, out _);
                var adjustedPromptAndSettings = namedTextCompletion.AdjustPromptAndRequestSettings(originalTest.Prompt, originalTest.RequestSettings, promptMultiConnectorSettings, multiTextCompletionSettings, logger);

                if (this.TestsTemperatureTransform != null)
                {
                    var temperatureUpdater = new SettingsUpdater<CompleteRequestSettings>(adjustedPromptAndSettings.requestSettings, MultiTextCompletionSettings.CloneRequestSettings);
                    adjustedPromptAndSettings.requestSettings = temperatureUpdater.ModifyIfChanged(settings => settings.Temperature, this.TestsTemperatureTransform, (settings, newTemp) => settings.Temperature = newTemp, out _);
                }

                var completions = await namedTextCompletion.TextCompletion.GetCompletionsAsync(adjustedPromptAndSettings.text, adjustedPromptAndSettings.requestSettings, cancellationToken).ConfigureAwait(false);

                var firstResult = completions[0];
                string result = await firstResult.GetCompletionAsync(cancellationToken).ConfigureAwait(false) ?? string.Empty;

                stopWatch.Stop();
                var duration = stopWatch.Elapsed;
                decimal textCompletionCost = namedTextCompletion.GetCost(adjustedPromptAndSettings.text, result);

                // For the evaluation task. We don't keep the adjusted settings since prompt type matching is based on the original prompt
                var connectorTest = ConnectorTest.Create(originalTest.Prompt, originalTest.RequestSettings, namedTextCompletion, result, duration, textCompletionCost);
                tests.Add(connectorTest);

                logger?.LogDebug("Generated Test results for connector {0}, duration: {1}\nTEST_PROMPT:\n{2}\nTEST_RESULT:\n{3} ", connectorTest.ConnectorName, connectorTest.Duration, connectorTest.Prompt, connectorTest.Result);
            }
            catch (AIException exception)
            {
                logger?.LogError(exception, "Failed to run test prompt with connector {2}\nException:{0}Prompt:\n{1} ", exception, exception.ToString(), originalTest.Prompt, namedTextCompletion.Name);
            }
        }
    }

    private MultiCompletionAnalysis SaveConnectorTestsReturnNeedEvaluate(List<ConnectorTest> tests, MultiCompletionAnalysis analysis, ILogger? logger, out bool needEvaluate)
    {
        bool UpdateTestsAndProbeEvaluate(MultiCompletionAnalysis multiCompletionAnalysis)
        {
            var originalTestPromptsToRemove = tests.Select(test => test.Prompt).Distinct();
            multiCompletionAnalysis.OriginalTests.RemoveAll(test => originalTestPromptsToRemove.Contains(test.Prompt));

            logger?.LogTrace("Found {0} tests", multiCompletionAnalysis.Tests.Count);
            multiCompletionAnalysis.Tests.AddRange(tests);
            bool needEvaluate = (this.EnableTestEvaluations)
                                && multiCompletionAnalysis.Tests.Count > 0
                                && (DateTime.Now - multiCompletionAnalysis.EvaluationTimestamp) > this.EvaluationPeriod
                                && multiCompletionAnalysis.OriginalTests.Count == 0
                                || (DateTime.Now - multiCompletionAnalysis.TestTimestamp) < this.TestsPeriod;
            if (needEvaluate)
            {
                multiCompletionAnalysis.EvaluationTimestamp = DateTime.Now;
            }

            return needEvaluate;
        }

        logger?.LogTrace("Loading Analysis file from {0} to update tests", this.AnalysisFilePath);

        analysis = this.LockLoadApplySaveProbeNext(analysis, UpdateTestsAndProbeEvaluate, out needEvaluate, logger);

        logger?.LogTrace("Saved {0} new test results to {1}", tests.Count, this.AnalysisFilePath);
        return analysis;
    }

    private async Task<List<ConnectorPromptEvaluation>> RunConnectorTestsEvaluationsAsync(List<ConnectorTest> tests, IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, ILogger? logger, CancellationToken cancellationToken)
    {
        var currentEvaluations = new ConcurrentBag<ConnectorPromptEvaluation>();
        logger?.LogTrace("Generating Evaluations from prompt test results");

        var tasks = new List<Task>();
        using SemaphoreSlim semaphore = new(this.MaxDegreeOfParallelismEvaluations);

        foreach (var connectorTest in tests)
        {
            tasks.Add(Task.Run(async () =>
            {
                await semaphore.WaitAsync(cancellationToken).ConfigureAwait(false);
                try
                {
                    var evaluation = await this.EvaluateConnectorTestAsync(connectorTest, namedTextCompletions, settings, logger, cancellationToken).ConfigureAwait(false);
                    if (evaluation != null)
                    {
                        currentEvaluations.Add(evaluation);
                    }
                }
                finally
                {
                    semaphore.Release();
                }
            }, cancellationToken));
        }

        await Task.WhenAll(tasks).ConfigureAwait(false);

        return currentEvaluations.ToList();
    }

    private async Task<ConnectorPromptEvaluation?> EvaluateConnectorTestAsync(ConnectorTest connectorTest, IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, ILogger? logger, CancellationToken cancellationToken)
    {
        NamedTextCompletion? vettingConnector = null;
        if (this.UseSelfVetting)
        {
            vettingConnector = namedTextCompletions.FirstOrDefault(c => c.Name == connectorTest.ConnectorName);
        }

        // Use primary connector for vetting by default
        vettingConnector ??= namedTextCompletions[0];

        var evaluation = await this.EvaluateConnectorTestWithCompletionAsync(vettingConnector, connectorTest, settings, logger, cancellationToken).ConfigureAwait(false);
        if (evaluation == null)
        {
            logger?.LogError("Evaluation could not be performed for connector {0}", connectorTest.ConnectorName);
        }

        logger?.LogDebug("Evaluated connector {0}, Vetted:{1} from \nPROMPT_EVALUATED:\n{2}\nRESULT_EVALUATED:{3}", evaluation?.Test.ConnectorName, evaluation?.IsVetted, evaluation?.Test.Prompt, evaluation?.Test.Result);

        return evaluation;
    }

    private MultiCompletionAnalysis SaveEvaluationsReturnNeedSuggestion(List<ConnectorPromptEvaluation> currentEvaluations, MultiCompletionAnalysis completionAnalysis, out bool needSuggestion, ILogger? logger)
    {
        bool UpdateEvaluationsAndProbeSuggestion(MultiCompletionAnalysis multiCompletionAnalysis)
        {
            var testTimestampsToRemove = currentEvaluations.Select(evaluation => evaluation.Test.Timestamp);
            multiCompletionAnalysis.Tests.RemoveAll(test => testTimestampsToRemove.Contains(test.Timestamp));
            logger?.LogTrace("Found {0} evaluations", multiCompletionAnalysis.Evaluations.Count);
            multiCompletionAnalysis.Evaluations.AddRange(currentEvaluations);
            bool needSuggestion = (this.EnableSuggestion
                                   && (this.UpdateSuggestedSettings || this.SaveSuggestedSettings))
                                  && multiCompletionAnalysis.Evaluations.Count > 0
                                  && (DateTime.Now - multiCompletionAnalysis.SuggestionTimestamp) > this.SuggestionPeriod
                                  && multiCompletionAnalysis.Tests.Count == 0
                                  || (DateTime.Now - multiCompletionAnalysis.EvaluationTimestamp) < this.EvaluationPeriod
                                  && multiCompletionAnalysis.OriginalTests.Count == 0
                                  || (DateTime.Now - multiCompletionAnalysis.TestTimestamp) < this.TestsPeriod;
            if (needSuggestion)
            {
                multiCompletionAnalysis.SuggestionTimestamp = DateTime.Now;
            }

            return needSuggestion;
        }

        logger?.LogTrace("Loading Analysis file from {0} to save evaluations", this.AnalysisFilePath);

        completionAnalysis = this.LockLoadApplySaveProbeNext(completionAnalysis, UpdateEvaluationsAndProbeSuggestion, out needSuggestion, logger);

        logger?.LogTrace("Saved {0} evaluations to {1}", currentEvaluations.Count, this.AnalysisFilePath);
        return completionAnalysis;
    }

    /// <summary>
    /// Computes new MultiTextCompletionSettings with prompt connector settings based on analysis of their evaluation .
    /// </summary>
    public SuggestionCompletedEventArgs ComputeNewSettingsFromAnalysis(IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, bool updateSettings, ILogger? logger, CancellationToken? cancellationToken = default)
    {
        // If not updating settings in-place, create a new instance
        var settingsToReturn = settings;
        if (!updateSettings)
        {
            settingsToReturn = JsonSerializer.Deserialize<MultiTextCompletionSettings>(JsonSerializer.Serialize(settings))!;
        }

        MultiCompletionAnalysis completionAnalysis = new();
        // Load evaluation results
        lock (this._analysisFileLock)
        {
            if (File.Exists(this.AnalysisFilePath))
            {
                var json = File.ReadAllText(this.AnalysisFilePath);
                completionAnalysis = JsonSerializer.Deserialize<MultiCompletionAnalysis>(json) ?? new MultiCompletionAnalysis();
            }
        }

        var evaluationsByPromptSettings = new Dictionary<PromptMultiConnectorSettings, List<ConnectorPromptEvaluation>>();
        foreach (var evaluation in completionAnalysis.Evaluations)
        {
            var promptSettings = settingsToReturn!.GetPromptSettings(evaluation.Test.Prompt, evaluation.Test.RequestSettings, out _);
            if (promptSettings.PromptType.Instances.Count < this.MaxInstanceNb && !promptSettings.PromptType.Instances.Contains(evaluation.Test.Prompt))
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
                    logger?.LogDebug("Connector  {0}, configured according to evaluations with level:{1} for \nPrompt type with signature:\n{2}", connectorName, promptConnectorSettings.VettingLevel, promptMultiConnectorSettings.PromptType.Signature.TextBeginning);
                }
            }
        }

        return new SuggestionCompletedEventArgs(completionAnalysis, settingsToReturn);
    }

    private MultiCompletionAnalysis LockLoadApplySaveProbeNext(MultiCompletionAnalysis analysis, Func<MultiCompletionAnalysis, bool> updateAndProbeTimespan, out bool runNextStep, ILogger? logger)
    {
        var currentAnalysis = analysis;

        lock (this._analysisFileLock)
        {
            if (File.Exists(this.AnalysisFilePath))
            {
                var json = File.ReadAllText(this.AnalysisFilePath);
                currentAnalysis = JsonSerializer.Deserialize<MultiCompletionAnalysis>(json) ?? currentAnalysis;
            }

            runNextStep = updateAndProbeTimespan(currentAnalysis);
            var jsonString = JsonSerializer.Serialize(currentAnalysis, new JsonSerializerOptions() { WriteIndented = true });
            File.WriteAllText(this.AnalysisFilePath, jsonString);
        }

        return currentAnalysis;
    }

    #endregion

}
