// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the settings used to configure the multi-completion analysis process.
/// </summary>
public class MultiCompletionAnalysisSettings
{
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
    /// Determine if self-vetting should be used
    /// </summary>
    public bool UseSelfVetting { get; set; } = false;

    /// <summary>
    /// The path to store analysis results
    /// </summary>
    public string AnalysisFilePath { get; set; } = ".\\MultiTextCompletion-analysis.json";

    /// <summary>
    /// Time period to conduct analysis
    /// </summary>
    public TimeSpan AnalysisPeriod { get; set; } = TimeSpan.FromMinutes(1);

    /// <summary>
    /// Duration before analysis is started when a new event is recorded
    /// </summary>
    public TimeSpan AnalysisDelay { get; set; } = TimeSpan.FromSeconds(1);

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
    /// Number of prompt tests to be run
    /// </summary>
    public int NbPromptTests { get; set; } = 10;

    /// <summary>
    /// The vetting prompt used in evaluation
    /// </summary>
    public string VettingPromptTemplate { get; set; } = DefaultVettingPromptTemplate;

    /// <summary>
    /// Request settings for the vetting process
    /// </summary>
    public CompleteRequestSettings VettingRequestSettings { get; set; } = DefaultVettingRequestSettings;

    /// <summary>
    /// Asynchronously evaluates a connector test, writes the evaluation to a file, and updates settings if necessary.
    /// </summary>
    public async Task EvaluatePromptConnectorsAsync(ConnectorTest originalTest, IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, ILogger? logger = null, CancellationToken cancellationToken = default)
    {
        var promptSettings = settings.GetPromptSettings(originalTest.Prompt, originalTest.RequestSettings);

        promptSettings.IsTesting = true;

        // Generate tests

        var tests = new List<ConnectorTest>();

        var connectorsToTest = promptSettings.GetCompletionsToTest(namedTextCompletions);

        foreach (NamedTextCompletion namedTextCompletion in connectorsToTest)
        {
            for (int i = 0; i < this.NbPromptTests; i++)
            {
                var stopWatch = Stopwatch.StartNew();
                string result = "";
                try
                {
                    var completions = await namedTextCompletion.TextCompletion.GetCompletionsAsync(originalTest.Prompt, originalTest.RequestSettings, cancellationToken).ConfigureAwait(false);

                    var firstResult = completions[0];

                    result = await firstResult.GetCompletionAsync(cancellationToken).ConfigureAwait(false) ?? string.Empty;

                    stopWatch.Stop();
                    var duration = stopWatch.Elapsed;

                    // For the management task
                    var connectorTest = ConnectorTest.Create(originalTest.Prompt, originalTest.RequestSettings, namedTextCompletion, result, duration);
                    tests.Add(connectorTest);
                }
                catch (Exception exception)
                {
                    logger?.LogError(exception, "Failed to test prompt with connector.\nPrompt:\n {0}\nConnector: {1} ", originalTest.Prompt, namedTextCompletion.Name);
                }
            }
        }

        // Generate evaluations

        var currentEvaluations = new List<ConnectorPromptEvaluation>();
        foreach (ConnectorTest connectorTest in tests)
        {
            NamedTextCompletion? vettingConnector = null;
            if (this.UseSelfVetting)
            {
                vettingConnector = namedTextCompletions.FirstOrDefault(c => c.Name == connectorTest.ConnectorName);
            }

            // Use primary connector for vetting by default
            vettingConnector ??= namedTextCompletions[0];

            for (int i = 0; i < this.NbPromptTests; i++)
            {
                var evaluation = await this.EvaluateConnectorTestWithCompletionAsync(vettingConnector, connectorTest, settings, cancellationToken).ConfigureAwait(false);
                if (evaluation == null)
                {
                    logger?.LogError("Evaluation could not be performed for connector {0}", connectorTest.ConnectorName);
                    break;
                }

                currentEvaluations.Add(evaluation);
            }
        }

        //Save evaluations to file

        var completionAnalysis = new MultiCompletionAnalysis();
        lock (this._analysisFileLock)
        {
            if (File.Exists(this.AnalysisFilePath))
            {
                var json = File.ReadAllText(this.AnalysisFilePath);
                completionAnalysis = JsonSerializer.Deserialize<MultiCompletionAnalysis>(json) ?? completionAnalysis;
            }

            completionAnalysis.Timestamp = DateTime.Now;
            completionAnalysis.Evaluations.AddRange(currentEvaluations);
            var jsonString = JsonSerializer.Serialize(completionAnalysis, new JsonSerializerOptions() { WriteIndented = true });
            File.WriteAllText(this.AnalysisFilePath, jsonString);
        }

        // If update or save suggested settings are enabled, suggest new settings from analysis and save them if needed
        if (this.UpdateSuggestedSettings || this.SaveSuggestedSettings && (DateTime.Now - completionAnalysis.Timestamp) > this.AnalysisPeriod)
        {
            var newSettings = this.ComputeNewSettingsFromAnalysis(namedTextCompletions, settings, this.UpdateSuggestedSettings, cancellationToken);
            if (this.SaveSuggestedSettings)
            {
                // Save the new settings
                var settingsJson = JsonSerializer.Serialize(newSettings, new JsonSerializerOptions() { WriteIndented = true });
                File.WriteAllText(this.MultiCompletionSettingsFilePath, settingsJson);
            }

            if (this.DeleteAnalysisFile)
            {
                lock (this._analysisFileLock)
                {
                    if (File.Exists(this.AnalysisFilePath))
                    {
                        File.Delete(this.AnalysisFilePath);
                    }
                }
            }
        }

        promptSettings.IsTesting = false;
    }

    /// <summary>
    /// Computes new MultiTextCompletionSettings with prompt connector settings based on analysis of their evaluation .
    /// </summary>
    public MultiTextCompletionSettings ComputeNewSettingsFromAnalysis(IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, bool updateSettings, CancellationToken? cancellationToken = default)
    {
        // If not updating settings in-place, create a new instance
        var settingsToReturn = settings;
        if (!updateSettings)
        {
            settingsToReturn = JsonSerializer.Deserialize<MultiTextCompletionSettings>(JsonSerializer.Serialize(settings));
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
            var promptSettings = settingsToReturn!.GetPromptSettings(evaluation.Test.Prompt, evaluation.Test.RequestSettings);
            if (promptSettings.PromptType.Instances.Count < this.NbPromptTests && !promptSettings.PromptType.Instances.Contains(evaluation.Test.Prompt))
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
                var vetted = evaluationsByMainConnector.All(e => e.IsVetted);
                var vettedVaried = !evaluationsByMainConnector.GroupBy(evaluation => evaluation.Test.Prompt).Any(grouping => grouping.Count() > 1);
                promptConnectorSettings.VettingLevel = vetted ? vettedVaried ? VettingLevel.OracleVaried : VettingLevel.Oracle : VettingLevel.Invalid;
            }
        }

        return settings;
    }

    /// <summary>
    /// Evaluates a ConnectorTest with a NamedTextCompletion instance and returns the evaluation.
    /// </summary>
    public async Task<ConnectorPromptEvaluation> EvaluateConnectorTestWithCompletionAsync(NamedTextCompletion completion, ConnectorTest connectorTest, MultiTextCompletionSettings settings, CancellationToken cancellationToken = default)
    {
        var prompt = this.VettingPromptTemplate.Replace("{prompt}", connectorTest.Prompt).Replace("{response}", connectorTest.Result);
        var stopWatch = Stopwatch.StartNew();
        var completionResult = await completion.TextCompletion.CompleteAsync(prompt, this.VettingRequestSettings, cancellationToken).ConfigureAwait(false) ?? "false";
        stopWatch.Stop();
        var elapsed = stopWatch.Elapsed;
        var isVetted = completionResult.Equals("true", StringComparison.OrdinalIgnoreCase);
        var toReturn = new ConnectorPromptEvaluation
        {
            Test = connectorTest,
            VettingConnector = completion.Name,
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
}
