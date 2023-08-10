// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the settings used to configure the multi-text completion process.
/// </summary>
public class MultiTextCompletionSettings
{
    /// <summary>
    /// Loads suggested settings from an analysis.
    /// If the file doesn't exist, it returns the current settings.
    /// </summary>
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

    /// <summary>
    /// Holds the settings for completion analysis process.
    /// </summary>
    public MultiCompletionAnalysisSettings AnalysisSettings { get; set; } = new();

    /// <summary>
    /// Represents the length to which prompts will be truncated for signature extraction.
    /// </summary>
    public int PromptTruncationLength { get; set; } = 20;

    /// <summary>
    /// By default, connectors instrumentation server side and client side avoids to trigger result evaluation for display. This is mostly harmless and this outputs the corresponding log for more comfort.
    /// </summary>
    public bool LogResult { get; set; } = false;

    /// <summary>
    /// List of settings for multiple connectors associated with each prompt type.
    /// </summary>
    public List<PromptMultiConnectorSettings> PromptMultiConnectorSettings { get; } = new();

    /// <summary>
    /// Comparer used to choose among vetted connectors.
    /// </summary>
    [JsonIgnore]
    public Func<PromptConnectorSettings, PromptConnectorSettings, int> ConnectorComparer { get; set; } = GetConnectorComparer(1, 1);

    /// <summary>
    /// Optionally transform the input prompts globally
    /// </summary>
    public PromptTransform? GlobalPromptTransform { get; set; }

    /// <summary>
    /// An optional creditor that will compute compound costs from the connectors settings and usage.
    /// </summary>
    public CallRequestCostCreditor? Creditor { get; set; }

    /// <summary>
    /// Returns settings for a given prompt.
    /// If settings for the prompt do not exist, new settings are created, added to the list, and returned.
    /// </summary>
    public PromptMultiConnectorSettings GetPromptSettings(string prompt, CompleteRequestSettings promptSettings, out bool isNew)
    {
        isNew = false;
        var toReturn = this.PromptMultiConnectorSettings.FirstOrDefault(s => s.PromptType.Signature.Matches(prompt, promptSettings));
        if (toReturn == null)
        {
            lock (this.PromptMultiConnectorSettings)
            {
                var newSignature = PromptSignature.ExtractFromPrompt(prompt, promptSettings, this.PromptTruncationLength);
                toReturn = new PromptMultiConnectorSettings()
                {
                    PromptType = new PromptType()
                    {
                        Instances = { prompt },
                        MaxInstanceNb = this.AnalysisSettings.NbPromptTests,
                        Signature = newSignature,
                        PromptName = newSignature.TextBeginning.Replace(" ", "_")
                    },
                };

                this.PromptMultiConnectorSettings.Add(toReturn);
                isNew = true;
            }
        }

        return toReturn;
    }

    /// <summary>
    /// this will reset the vetting level of all connectors for all prompt types, and empty recorded instances, such that test collection and vetting analysis will be triggered if enabled.
    /// </summary>
    public void ResetPromptVetting()
    {
        foreach (var promptMultiConnectorSetting in this.PromptMultiConnectorSettings)
        {
            promptMultiConnectorSetting.PromptType.Instances.Clear();
            foreach (var pairConnectorSetting
                     in promptMultiConnectorSetting.ConnectorSettingsDictionary)
            {
                pairConnectorSetting.Value.VettingLevel = VettingLevel.None;
            }
        }
    }

    /// <summary>
    /// Builds a comparer to compare two connectors given the respective weight attached to to their average duration and average cost fractions.
    /// </summary>
    /// <param name="durationWeight">the weight of the duration gains in proportion</param>
    /// <param name="costWeight">the weight of the cost gains in proportion</param>
    public static Func<PromptConnectorSettings, PromptConnectorSettings, int> GetConnectorComparer(double durationWeight, double costWeight)
    {
        return (a, b) =>
        {
            double? durationCoefficient = null;
            if (a.AverageDuration > TimeSpan.Zero && b.AverageDuration > TimeSpan.Zero)
            {
                durationCoefficient = b.AverageDuration.Ticks / (double)a.AverageDuration.Ticks;
            }

            double? costCoefficient = null;
            if (a.AverageCost > 0 && b.AverageCost > 0)
            {
                costCoefficient = (double)b.AverageCost / (double)a.AverageCost;
            }

            var doubledResult = (costWeight * costCoefficient ?? 1 + durationWeight * durationCoefficient ?? 1) / (costWeight + durationWeight);
            var intResult = doubledResult <= 1 ? Math.Abs(doubledResult - 1) < 0.01 ? 0 : 1 : -1;
            return intResult;
        };
    }

    /// <summary>
    /// Static function that clones a <see cref="CompleteRequestSettings"/> object.
    /// </summary>
    public static CompleteRequestSettings CloneRequestSettings(CompleteRequestSettings requestSettings)
    {
        return new CompleteRequestSettings()
        {
            MaxTokens = requestSettings.MaxTokens,
            ResultsPerPrompt = requestSettings.ResultsPerPrompt,
            ChatSystemPrompt = requestSettings.ChatSystemPrompt,
            FrequencyPenalty = requestSettings.FrequencyPenalty,
            PresencePenalty = requestSettings.PresencePenalty,
            StopSequences = requestSettings.StopSequences,
            Temperature = requestSettings.Temperature,
            TokenSelectionBiases = requestSettings.TokenSelectionBiases,
            TopP = requestSettings.TopP,
        };
    }
}
