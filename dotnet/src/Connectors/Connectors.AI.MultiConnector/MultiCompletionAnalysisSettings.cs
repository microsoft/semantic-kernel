// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
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
    /// Indicates whether to update suggested settings after analysis
    /// </summary>
    public bool UpdateSuggestedSettings { get; set; } = true;

    /// <summary>
    /// Indicates whether to save suggested settings after analysis
    /// </summary>
    public bool SaveSuggestedSettings { get; set; } = true;

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
    public string VettingPrompt { get; set; } = @"Following are an LLM prompt and a corresponding response from the LLM model. Please indicate whether the response is correct or not. Answer with true or false.
PROMPT:
-------
{prompt}
RESPONSE:
---------
{reponse}
RESPONSE IS VALID?
---------------
";

    /// <summary>
    /// Request settings for the vetting process
    /// </summary>
    public CompleteRequestSettings VettingRequestSettings { get; set; } = new();

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

                var completions = await namedTextCompletion.TextCompletion.GetCompletionsAsync(originalTest.Prompt, originalTest.RequestSettings, cancellationToken).ConfigureAwait(false);

                var firstResult = completions[0];

                string result = await firstResult.GetCompletionAsync(cancellationToken).ConfigureAwait(false) ?? string.Empty;

                stopWatch.Stop();
                var duration = stopWatch.Elapsed;

                // For the management task
                var connectorTest = new ConnectorTest
                {
                    Prompt = originalTest.Prompt,
                    RequestSettings = originalTest.RequestSettings,
                    ConnectorName = namedTextCompletion.Name,
                    Result = result,
                    Duration = duration,
                };
                tests.Add(connectorTest);
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
            if (!File.Exists(this.AnalysisFilePath))
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
            var evaluationsByConnector = promptEvaluations.Value.GroupBy(e => e.Test.ConnectorName);
            foreach (var connectorEvaluations in evaluationsByConnector)
            {
                var connectorName = connectorEvaluations.Key;
                var promptConnectorSettings = promptEvaluations.Key.GetConnectorSettings(connectorName);

                promptConnectorSettings.Evaluations = connectorEvaluations.ToList();
                promptConnectorSettings.AverageDuration = TimeSpan.FromMilliseconds(connectorEvaluations.Average(e => e.Test.Duration.TotalMilliseconds));
                var evaluationsByMainConnector = connectorEvaluations.GroupBy(e => e.VettingConnector).OrderByDescending(grouping => grouping.Count()).First();
                promptConnectorSettings.VettingConnector = evaluationsByMainConnector.Key;
                var vetted = evaluationsByMainConnector.All(e => e.IsVetted);
                var vettedVaried = !evaluationsByMainConnector.GroupBy(evaluation => evaluation.Test.Prompt).Any(grouping => grouping.Count() > 1);
                promptConnectorSettings.VettingLevel = vetted ? vettedVaried ? VettingLevel.Oracle : VettingLevel.OracleVaried : VettingLevel.Invalid;
            }
        }

        return settings;
    }

    /// <summary>
    /// Evaluates a ConnectorTest with a NamedTextCompletion instance and returns the evaluation.
    /// </summary>
    public async Task<ConnectorPromptEvaluation> EvaluateConnectorTestWithCompletionAsync(NamedTextCompletion completion, ConnectorTest connectorTest, MultiTextCompletionSettings settings, CancellationToken cancellationToken = default)
    {
        var prompt = this.VettingPrompt.Replace("{prompt}", connectorTest.Prompt).Replace("{response}", connectorTest.Result);
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
}
