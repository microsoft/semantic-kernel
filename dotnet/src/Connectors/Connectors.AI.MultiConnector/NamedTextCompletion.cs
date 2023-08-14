// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents a text completion provider instance with the corresponding given name.
/// </summary>
[DebuggerDisplay("{Name}")]
public class NamedTextCompletion
{
    /// <summary>
    /// Gets or sets the name of the text completion provider.
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    /// text completion provider instance, to be used for prompt answering and testing.
    /// </summary>
    public ITextCompletion TextCompletion { get; set; }

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Optionally transform the input prompt specifically for the model
    /// </summary>
    public PromptTransform? PromptTransform { get; set; }

    /// <summary>
    /// The model might support a different range of temperature than SK (is 0 legal?) This optional function can help keep the temperature in the model's range.
    /// </summary>
    [JsonIgnore]
    public Func<double, double>? TemperatureTransform { get; set; }

    /// <summary>
    /// The model might support a different range of settings than SK. This optional function can help keep the settings in the model's range.
    /// </summary>
    [JsonIgnore]
    public Func<CompleteRequestSettings, CompleteRequestSettings>? RequestSettingsTransform { get; set; }

    /// <summary>
    /// The strategy to ensure request settings max token don't exceed the model's total max token.
    /// </summary>
    public MaxTokensAdjustment MaxTokensAdjustment { get; set; } = MaxTokensAdjustment.Percentage;

    /// <summary>
    /// When <see cref="MaxTokensAdjustment"/> is set to <see cref="MaxTokensAdjustment.Percentage"/>, this is the percentage of the model's max tokens available for completion settings.
    /// </summary>
    public int MaxTokensReservePercentage { get; set; } = 80;

    /// <summary>
    /// Cost per completion request.
    /// </summary>
    public decimal CostPerRequest { get; set; }

    /// <summary>
    /// Cost for 1000 completion token from request + result text.
    /// </summary>
    public decimal? CostPer1000Token { get; set; }

    [JsonIgnore]
    public Func<string, int>? TokenCountFunc { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="NamedTextCompletion"/> class.
    /// </summary>
    /// <param name="name">The name of the text completion provider.</param>
    /// <param name="textCompletion">The text completion provider.</param>
    public NamedTextCompletion(string name, ITextCompletion textCompletion)
    {
        this.Name = name;
        this.TextCompletion = textCompletion;
    }

    public decimal GetCost(string text, string result)
    {
        var tokenCount = (this.TokenCountFunc ?? (s => 0))(text + result);
        decimal tokenCost = (this.CostPer1000Token ?? 0) * tokenCount / 1000;
        var toReturn = this.CostPerRequest + tokenCost;
        return toReturn;
    }

    /// <summary>
    /// Adjusts the request max tokens and temperature settings based on the completion max token supported.
    /// </summary>
    public CompletionJob AdjustPromptAndRequestSettings(CompletionJob completionJob,
        PromptConnectorSettings promptConnectorSettings,
        PromptMultiConnectorSettings promptMultiConnectorSettings,
        MultiTextCompletionSettings multiTextCompletionSettings,
        ILogger? logger)
    {
        logger?.LogTrace("Adjusting prompt and settings for connector {0} and prompt type {1}", this.Name, promptMultiConnectorSettings.PromptType.Signature.PromptStart);

        // Adjusting settings

        var adjustedSettings = completionJob.RequestSettings;

        var adjustedSettingsModifier = new SettingsUpdater<CompleteRequestSettings>(adjustedSettings, MultiTextCompletionSettings.CloneRequestSettings);

        bool valueChanged = false;
        if (this.MaxTokens != null && completionJob.RequestSettings.MaxTokens != null)
        {
            int? ComputeMaxTokens(int? initialValue)
            {
                var newMaxTokens = initialValue;
                if (newMaxTokens != null)
                {
                    switch (this.MaxTokensAdjustment)
                    {
                        case MaxTokensAdjustment.Percentage:
                            newMaxTokens = Math.Min(newMaxTokens.Value, this.MaxTokens.Value * this.MaxTokensReservePercentage / 100);
                            break;
                        case MaxTokensAdjustment.CountInputTokens:
                            if (this.TokenCountFunc != null)
                            {
                                newMaxTokens = Math.Min(newMaxTokens.Value, this.MaxTokens.Value - this.TokenCountFunc(completionJob.Prompt));
                            }
                            else
                            {
                                logger?.LogWarning("Inconsistency found with named Completion {0}: Max Token adjustment is configured to account for input token number but no Token count function was defined. MaxToken settings will be left untouched", this.Name);
                            }

                            break;
                    }
                }

                return newMaxTokens;
            }

            adjustedSettings = adjustedSettingsModifier.ModifyIfChanged(r => r.MaxTokens, ComputeMaxTokens, (setting, value) => setting.MaxTokens = value, out valueChanged);

            if (valueChanged)
            {
                logger?.LogDebug("Changed request max token from {0} to {1}", completionJob.RequestSettings.MaxTokens.Value, adjustedSettings.MaxTokens);
            }
        }

        if (this.TemperatureTransform != null)
        {
            adjustedSettings = adjustedSettingsModifier.ModifyIfChanged(r => r.Temperature, this.TemperatureTransform, (setting, value) => setting.Temperature = value, out valueChanged);

            if (valueChanged)
            {
                logger?.LogDebug("Changed temperature from {0} to {1}", completionJob.RequestSettings.Temperature, adjustedSettings.Temperature);
            }
        }

        if (this.RequestSettingsTransform != null)
        {
            adjustedSettings = this.RequestSettingsTransform(completionJob.RequestSettings);
            logger?.LogTrace("Applied request settings transform");
        }

        //Adjusting prompt

        var adjustedPrompt = completionJob.Prompt;

        if (multiTextCompletionSettings.GlobalPromptTransform != null)
        {
            adjustedPrompt = multiTextCompletionSettings.GlobalPromptTransform.TransformFunction(adjustedPrompt, multiTextCompletionSettings.GlobalParameters);
            logger?.LogTrace("Applied global settings prompt transform");
        }

        if (promptMultiConnectorSettings.PromptTypeTransform != null && promptConnectorSettings.ApplyPromptTypeTransform)
        {
            adjustedPrompt = promptMultiConnectorSettings.PromptTypeTransform.TransformFunction(adjustedPrompt, multiTextCompletionSettings.GlobalParameters);
            logger?.LogTrace("Applied prompt type settings prompt transform");
        }

        if (promptConnectorSettings.PromptConnectorTypeTransform != null)
        {
            adjustedPrompt = promptConnectorSettings.PromptConnectorTypeTransform.TransformFunction(adjustedPrompt, multiTextCompletionSettings.GlobalParameters);
            logger?.LogTrace("Applied prompt connector type settings prompt transform");
        }

        if (this.PromptTransform != null && (promptMultiConnectorSettings.ApplyModelTransform || promptConnectorSettings.EnforceModelTransform))
        {
            adjustedPrompt = this.PromptTransform.TransformFunction(adjustedPrompt, multiTextCompletionSettings.GlobalParameters);
            logger?.LogTrace("Applied named connector settings transform");
        }

        return new CompletionJob(adjustedPrompt, adjustedSettings);
    }
}
