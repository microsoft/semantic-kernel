// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

public class NamedTextCompletion
{
    public string Name { get; set; }
    public ITextCompletion TextCompletion { get; set; }

    public NamedTextCompletion(string name, ITextCompletion textCompletion)
    {
        this.Name = name;
        this.TextCompletion = textCompletion;
    }
}

public class PromptSignature
{
    private Regex? _compiledRegex;
    private const float FloatComparisonTolerance = 2 * float.Epsilon;
    public CompleteRequestSettings RequestSettings { get; set; }
    public string TextBeginning { get; set; }

    public string? MatchingRegex { get; set; }

    private Regex? CompiledRegex
    {
        get
        {
            if (this._compiledRegex == null && this.MatchingRegex?.Length > 0)
            {
                this._compiledRegex = new Regex(this.MatchingRegex, RegexOptions.Compiled | RegexOptions.IgnoreCase);
            }

            return this._compiledRegex;
        }
    }

    public PromptSignature()
    {
        this.RequestSettings = new();
        this.TextBeginning = string.Empty;
    }

    public PromptSignature(CompleteRequestSettings requestSettings, string textBeginning)
    {
        this.RequestSettings = requestSettings;
        this.TextBeginning = textBeginning;
    }

    public static PromptSignature ExtractFromPrompt(string prompt, CompleteRequestSettings settings, int truncationLength)
    {
        return new PromptSignature(settings, prompt.Substring(0, truncationLength));
    }

    public bool Matches(string prompt, CompleteRequestSettings promptSettings)
    {
        return (this.MatchSettings(promptSettings) && (this.CompiledRegex?.IsMatch(prompt) ??
                                                       prompt.StartsWith(this.TextBeginning, StringComparison.OrdinalIgnoreCase)));
    }

    private bool MatchSettings(CompleteRequestSettings promptSettings)
    {
        return this.RequestSettings.MaxTokens == promptSettings.MaxTokens &&
               Math.Abs(this.RequestSettings.Temperature - promptSettings.Temperature) < FloatComparisonTolerance &&
               Math.Abs(this.RequestSettings.TopP - promptSettings.TopP) < FloatComparisonTolerance &&
               this.RequestSettings.StopSequences.SequenceEqual(promptSettings.StopSequences) &&
               Math.Abs(this.RequestSettings.PresencePenalty - promptSettings.PresencePenalty) < FloatComparisonTolerance &&
               Math.Abs(this.RequestSettings.FrequencyPenalty - promptSettings.FrequencyPenalty) < FloatComparisonTolerance &&
               this.RequestSettings.ChatSystemPrompt == promptSettings.ChatSystemPrompt &&
               this.RequestSettings.ResultsPerPrompt == promptSettings.ResultsPerPrompt;
    }
}

public class PromptType
{
    public string PromptName { get; set; } = "";

    public List<string> Instances { get; } = new();

    public PromptSignature Signature { get; set; } = new();
}

public class TestEvent
{
    public DateTime Timestamp { get; set; } = DateTime.Now;
    public TimeSpan Duration { get; set; }
}

public class ConnectorTest : TestEvent
{
    public string ConnectorName { get; set; } = "";

    public string Prompt { get; set; } = "";

    public CompleteRequestSettings RequestSettings { get; set; } = new();

    public string Result { get; set; } = "";
}

public class ConnectorPromptEvaluation : TestEvent
{
    public ConnectorTest Test { get; set; } = new();
    public string VettingConnector { get; set; } = "";

    public bool IsVetted { get; set; }
}

public enum VettingLevel
{
    Invalid = -1,
    None = 0,
    Oracle = 3,
    OracleVaried = 4
}

public class PromptConnectorSettings
{
    public VettingLevel VettingLevel { get; set; } = VettingLevel.None;

    public string VettingConnector { get; set; } = "";

    public TimeSpan AverageDuration { get; set; }

    public List<ConnectorPromptEvaluation> Evaluations { get; set; } = new();
}

public class PromptMultiConnectorSettings
{
    public PromptType PromptType { get; set; } = new();

    public Dictionary<string, PromptConnectorSettings> ConnectorSettingsDictionary { get; } = new();

    internal static ConcurrentDictionary<string, bool> IsTesting = new();

    public PromptConnectorSettings GetConnectorSettings(string connectorName)
    {
        if (!this.ConnectorSettingsDictionary.TryGetValue(connectorName, out var promptConnectorSettings))
        {
            promptConnectorSettings = new PromptConnectorSettings();
            this.ConnectorSettingsDictionary[connectorName] = promptConnectorSettings;
        }

        return promptConnectorSettings;
    }

    public NamedTextCompletion SelectAppropriateTextCompletion(IReadOnlyList<NamedTextCompletion> namedTextCompletions)
    {
        // connectors are tested in reverse order of their registration, secondary connectors being prioritized over primary ones
        foreach (var namedTextCompletion in namedTextCompletions.Reverse())
        {
            if (this.ConnectorSettingsDictionary.TryGetValue(namedTextCompletion.Name, out PromptConnectorSettings? value))
            {
                if (value?.VettingLevel > 0)
                {
                    return namedTextCompletion;
                }
            }
        }

        // if no vetted connector is found, return the first primary one
        return namedTextCompletions[0];
    }
}

public class MultiCompletionAnalysis : TestEvent
{
    public List<ConnectorPromptEvaluation> Evaluations { get; set; } = new();
}

public class MultiCompletionAnalysisSettings
{
    private object _analysisFileLock = new();

    public bool EnableAnalysis { get; set; } = false;

    public bool UseSelfVetting { get; set; } = false;

    public string AnalysisFilePath { get; set; } = ".\\MultiTextCompletion-analysis.json";

    public TimeSpan AnalysisPeriod { get; set; } = TimeSpan.FromMinutes(1);

    public bool UpdateSuggestedSettings { get; set; } = true;

    public bool SaveSuggestedSettings { get; set; } = true;

    public string MultiCompletionSettingsFilePath { get; set; } = ".\\MultiTextCompletionSettings.json";

    public int NbPromptTests { get; set; } = 10;

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

    public CompleteRequestSettings VettingRequestSettings { get; set; } = new();


    public async Task EvaluateConnectorTestAsync(ConnectorTest connectorTest, IReadOnlyList<NamedTextCompletion> namedTextCompletions, MultiTextCompletionSettings settings, ILogger? logger = null, CancellationToken cancellationToken = default)
    {
        // Generate evaluation

        NamedTextCompletion? vettingConnector = null;
        if (this.UseSelfVetting)
        {
            vettingConnector = namedTextCompletions.FirstOrDefault(c => c.Name == connectorTest.ConnectorName);
        }

        // Use primary connector for vetting by default
        vettingConnector ??= namedTextCompletions[0];

        var currentEvaluations = new List<ConnectorPromptEvaluation>();
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
    }

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

public class MultiTextCompletionSettings
{
    public MultiTextCompletionSettings LoadSuggestedSettingsFromAnalysis()
    {
        string analysisSettingsMultiCompletionSettingsFilePath = this.AnalysisSettings.MultiCompletionSettingsFilePath;
        if (!File.Exists(analysisSettingsMultiCompletionSettingsFilePath))
        {
            return this;
        }

        string readAllText = File.ReadAllText(analysisSettingsMultiCompletionSettingsFilePath);
        MultiTextCompletionSettings? loadSuggestedAnalysisSettings = JsonSerializer.Deserialize<MultiTextCompletionSettings>(readAllText);
        return loadSuggestedAnalysisSettings ?? this;
    }

    public MultiCompletionAnalysisSettings AnalysisSettings { get; } = new();

    public int PromptTruncationLength { get; set; } = 50;

    public List<PromptMultiConnectorSettings> PromptMultiConnectorSettings { get; } = new();

    public PromptMultiConnectorSettings GetPromptSettings(string prompt, CompleteRequestSettings promptSettings)
    {
        var toReturn = this.PromptMultiConnectorSettings.FirstOrDefault(s => s.PromptType.Signature.Matches(prompt, promptSettings));
        if (toReturn == null)
        {
            var newSignature = PromptSignature.ExtractFromPrompt(prompt, promptSettings, this.PromptTruncationLength);
            toReturn = new PromptMultiConnectorSettings()
            {
                PromptType = new PromptType()
                {
                    Instances = { prompt },
                    Signature = newSignature,
                    PromptName = newSignature.TextBeginning.Replace(" ", "_")
                },
            };
            lock (this.PromptMultiConnectorSettings)
            {
                this.PromptMultiConnectorSettings.Add(toReturn);
            }
        }

        return toReturn;
    }
}

public class MultiTextCompletion : ITextCompletion
{
    private readonly ILogger? _logger;
    private readonly IReadOnlyList<NamedTextCompletion> _textCompletions;
    private readonly MultiTextCompletionSettings _settings;
    private readonly Channel<ConnectorTest> _connectorTestChannel;

    public MultiTextCompletion(MultiTextCompletionSettings settings, NamedTextCompletion mainTextCompletion, CancellationToken? completionsManagerCancellationToken, ILogger? logger = null, params NamedTextCompletion[] otherCompletions)
    {
        this._settings = settings;
        this._logger = logger;
        this._textCompletions = new[] { mainTextCompletion }.Concat(otherCompletions).ToArray();
        this._connectorTestChannel = Channel.CreateUnbounded<ConnectorTest>();
        this.StartManagementTask(completionsManagerCancellationToken ?? CancellationToken.None);
    }

    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        var promptSettings = this._settings.GetPromptSettings(text, requestSettings);
        var textCompletion = promptSettings.SelectAppropriateTextCompletion(this._textCompletions);

        var stopWatch = Stopwatch.StartNew();

        var completions = await textCompletion.TextCompletion.GetCompletionsAsync(text, requestSettings, cancellationToken).ConfigureAwait(false);

        if (textCompletion.Name != this._textCompletions[0].Name &&
            promptSettings.GetConnectorSettings(textCompletion.Name).VettingLevel == VettingLevel.None &&
            !PromptMultiConnectorSettings.IsTesting.ContainsKey(textCompletion.Name))
        {
            PromptMultiConnectorSettings.IsTesting.TryAdd(textCompletion.Name, true);
            await this.CollectResultForTestAsync(text, requestSettings, cancellationToken, completions, stopWatch, textCompletion).ConfigureAwait(false);
            PromptMultiConnectorSettings.IsTesting.TryRemove(textCompletion.Name, out _);
        }

        return completions;
    }

    private async Task CollectResultForTestAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken, IReadOnlyList<ITextResult> completions, Stopwatch stopWatch, NamedTextCompletion textCompletion)
    {
        var firstResult = completions[0];

        string result = await firstResult.GetCompletionAsync(cancellationToken).ConfigureAwait(false) ?? string.Empty;

        stopWatch.Stop();
        var duration = stopWatch.Elapsed;

        // For the management task
        var connectorTest = new ConnectorTest
        {
            Prompt = text,
            RequestSettings = requestSettings,
            ConnectorName = textCompletion.Name,
            Result = result,
            Duration = duration,
        };
        this.AppendConnectorTest(connectorTest);
    }

    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        var promptSettings = this._settings.GetPromptSettings(text, requestSettings);
        var textCompletion = promptSettings.SelectAppropriateTextCompletion(this._textCompletions);

        var result = textCompletion.TextCompletion.GetStreamingCompletionsAsync(text, requestSettings, cancellationToken);

        _ = this.CollectStreamingTestResultAsync(text, requestSettings, textCompletion, result, cancellationToken);

        return result;
    }

    private async Task CollectStreamingTestResultAsync(string text, CompleteRequestSettings requestSettings, NamedTextCompletion textCompletion, IAsyncEnumerable<ITextStreamingResult> results, CancellationToken cancellationToken)
    {
        var stopWatch = Stopwatch.StartNew();

        var collectedResult = new StringBuilder();
        // The test result will be collected when it becomes available.
        await foreach (var result in results.WithCancellation(cancellationToken))
        {
            collectedResult.Append(await result.GetCompletionAsync(cancellationToken).ConfigureAwait(false));
        }

        stopWatch.Stop();
        var duration = stopWatch.Elapsed;

        var connectorTest = new ConnectorTest
        {
            Prompt = text,
            RequestSettings = requestSettings,
            ConnectorName = textCompletion.Name,
            Result = collectedResult.ToString(),
            Duration = duration,
        };
        this.AppendConnectorTest(connectorTest);
    }

    private void StartManagementTask(CancellationToken cancellationToken)
    {
        Task.Factory.StartNew(
            async () =>
            {
                while (!cancellationToken.IsCancellationRequested)
                {
                    await this.OptimizeCompletionsAsync(cancellationToken).ConfigureAwait(false);
                }
            },
            cancellationToken,
            TaskCreationOptions.LongRunning,
            TaskScheduler.Default);
    }

    private async Task OptimizeCompletionsAsync(CancellationToken cancellationToken)
    {
        try
        {
            while (await this._connectorTestChannel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false))
            {
                while (this._connectorTestChannel.Reader.TryRead(out var connectorTest))
                {
                    if (!cancellationToken.IsCancellationRequested)
                    {
                        // TODO: start the collection and optimization
                        // Evaluate the test
                        await this._settings.AnalysisSettings.EvaluateConnectorTestAsync(connectorTest, this._textCompletions, this._settings, this._logger, cancellationToken).ConfigureAwait(false);
                    }
                }
            }
        }
        catch (OperationCanceledException exception)
        {
            this._logger?.LogTrace(message: "OptimizeCompletionsAsync Optimize task was cancelled", exception: exception);
        }
    }

    private void AppendConnectorTest(ConnectorTest connectorTest)
    {
        this._connectorTestChannel.Writer.TryWrite(connectorTest);
    }
}
