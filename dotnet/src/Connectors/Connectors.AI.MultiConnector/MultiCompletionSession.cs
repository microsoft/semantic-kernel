// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the state variables that are built and processed within a blocking or streaming call to the <see cref="MultiTextCompletion"/>.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay}")]
public class MultiCompletionSession
{
    public MultiCompletionSession(CompletionJob completionJob,
        PromptMultiConnectorSettings promptSettings,
        bool isNewPrompt,
        NamedTextCompletion namedTextCompletion,
        IReadOnlyList<NamedTextCompletion> availableCompletions,
        PromptConnectorSettings promptConnectorSettings,
        MultiTextCompletionSettings multiConnectorSettings,
        ILogger? logger)
    {
        this.MultiConnectorSettings = multiConnectorSettings;
        this.PromptSettings = promptSettings;
        this.InputJob = completionJob;
        this.CallJob = completionJob;
        this.IsNewPrompt = isNewPrompt;
        this.NamedTextCompletion = namedTextCompletion;
        this.AvailableCompletions = availableCompletions;
        this.PromptConnectorSettings = promptConnectorSettings;
        this.Stopwatch = Stopwatch.StartNew();
        this.Logger = logger;
        this.Context = new();
        this.ResultProducer = new AsyncLazy<string>(() => "", CancellationToken.None);
        this.Context = this.CreateSessionContext();
    }

    /// <summary>
    /// This initializes a new dictionary with the global parameters from the <see cref="MultiTextCompletionSettings"/>. No dynamic transforms are applied.
    /// </summary>
    /// <param name="multiConnectorSettings"></param>
    /// <returns></returns>
    public static Dictionary<string, object> CreateSimpleContext(MultiTextCompletionSettings multiConnectorSettings)
    {
        return multiConnectorSettings.GlobalParameters.ToDictionary(kvp => kvp.Key, kvp => (object)kvp.Value);
    }

    private Dictionary<string, object> CreateSessionContext()
    {
        var newContext = CreateSimpleContext(this.MultiConnectorSettings);
        if (this.MultiConnectorSettings.ContextProvider != null)
        {
            foreach (var kvp in this.MultiConnectorSettings.ContextProvider(this))
            {
                if (newContext.ContainsKey(kvp.Key))
                {
                    this.Logger?.LogWarning("Context provider is overriding a key already defined in the Global Parameters: {0}", kvp.Key);
                    newContext[kvp.Key] = kvp.Value;
                }
                else
                {
                    newContext.Add(kvp.Key, kvp.Value);
                }
            }
        }

        return newContext;
    }

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay => $"{this.PromptSettings.PromptType.PromptName} - {this.NamedTextCompletion.Name}";

    /// <summary>
    /// The <see cref="MultiTextCompletionSettings"/> that are passed to <see cref="MultiTextCompletion"/>.
    /// </summary>
    public MultiTextCompletionSettings MultiConnectorSettings { get; set; }

    /// <summary>
    /// The <see cref="PromptMultiConnectorSettings"/> that are obtained by matching the input prompt to the available Prompt Settings in <see cref="MultiTextCompletion"/>.
    /// </summary>
    public PromptMultiConnectorSettings PromptSettings { get; set; }

    /// <summary>
    /// The input prompt that is passed to <see cref="MultiTextCompletion"/>.
    /// </summary>
    public CompletionJob InputJob { get; set; }

    /// <summary>
    /// The input prompt that is passed to the individual LLM by the <see cref="MultiTextCompletion"/> and may be modified by various settings.
    /// </summary>
    public CompletionJob CallJob { get; set; }

    ///// <summary>
    ///// The <see cref="CompleteRequestSettings"/> that are passed to <see cref="MultiTextCompletion"/>.
    ///// </summary>
    //public CompleteRequestSettings InputRequestSettings { get; set; }

    ///// <summary>
    ///// The <see cref="CompleteRequestSettings"/> that are passed to the individual LLM by the <see cref="MultiTextCompletion"/> and may be modified by various settings.
    ///// </summary>
    //public CompleteRequestSettings CallRequestSettings { get; set; }

    /// <summary>
    /// A flag that indicates whether the input prompt type identified has a prior configuration or not.
    /// </summary>
    public bool IsNewPrompt { get; set; }

    /// <summary>
    /// The <see cref="NamedTextCompletion"/> that was elicited to answer the call to the <see cref="MultiTextCompletion"/>.
    /// </summary>
    public NamedTextCompletion NamedTextCompletion { get; set; }

    /// <summary>
    /// The list of all available <see cref="NamedTextCompletion"/>.
    /// </summary>
    public IReadOnlyList<NamedTextCompletion> AvailableCompletions { get; set; }

    /// <summary>
    /// The <see cref="PromptConnectorSettings"/> that correspond to the current Prompt settings and the chosen Text Completion.
    /// </summary>
    public PromptConnectorSettings PromptConnectorSettings { get; set; }

    /// <summary>
    /// The <see cref="System.Diagnostics.Stopwatch"/> that is used to measure the time taken to complete the call to the <see cref="MultiTextCompletion"/>.
    /// </summary>
    public Stopwatch Stopwatch { get; set; }

    /// <summary>
    /// Some operations require to pick on the result, some others not. This property is updated with completion result which is only deferred if needed.
    /// </summary>
    public AsyncLazy<string> ResultProducer { get; set; }

    /// <summary>
    /// Optional logger to be used for logging intermediate steps.
    /// </summary>
    public ILogger? Logger { get; set; }

    /// <summary>
    /// MultiCompletion Session Context
    /// </summary>
    public Dictionary<string, object> Context { get; set; }

    /// <summary>
    /// Adjusts prompt and request settings according to session parameters.
    /// </summary>
    public void AdjustPromptAndRequestSettings()
    {
        this.CallJob = AdjustPromptAndRequestSettings(this);
    }

    /// <summary>
    /// Adjusts prompt and request settings according to session parameters.
    /// </summary>
    public static CompletionJob AdjustPromptAndRequestSettings(MultiCompletionSession multiCompletionSession)
    {
        multiCompletionSession.Logger?.LogTrace("Adjusting prompt and settings for connector {0} and prompt type {1}", multiCompletionSession.NamedTextCompletion.Name, Json.Encode(multiCompletionSession.PromptSettings.PromptType.Signature.PromptStart, true));

        //Adjusting prompt

        var adjustedPrompt = multiCompletionSession.InputJob.Prompt;

        if (multiCompletionSession.MultiConnectorSettings.GlobalPromptTransform != null)
        {
            adjustedPrompt = multiCompletionSession.MultiConnectorSettings.GlobalPromptTransform.TransformFunction(adjustedPrompt, multiCompletionSession.Context);
            multiCompletionSession.Logger?.LogTrace("Applied global settings prompt transform");
        }

        if (multiCompletionSession.PromptSettings.PromptTypeTransform != null && multiCompletionSession.PromptConnectorSettings.ApplyPromptTypeTransform)
        {
            adjustedPrompt = multiCompletionSession.PromptSettings.PromptTypeTransform.TransformFunction(adjustedPrompt, multiCompletionSession.Context);
            multiCompletionSession.Logger?.LogTrace("Applied prompt type settings prompt transform");
        }

        if (multiCompletionSession.PromptConnectorSettings.PromptConnectorTypeTransform != null)
        {
            adjustedPrompt = multiCompletionSession.PromptConnectorSettings.PromptConnectorTypeTransform.TransformFunction(adjustedPrompt, multiCompletionSession.Context);
            multiCompletionSession.Logger?.LogTrace("Applied prompt connector type settings prompt transform");
        }

        if (multiCompletionSession.NamedTextCompletion.PromptTransform != null && (multiCompletionSession.PromptSettings.ApplyModelTransform || multiCompletionSession.PromptConnectorSettings.EnforceModelTransform))
        {
            adjustedPrompt = multiCompletionSession.NamedTextCompletion.PromptTransform.TransformFunction(adjustedPrompt, multiCompletionSession.Context);
            multiCompletionSession.Logger?.LogTrace("Applied named connector settings transform");
        }

        // Adjusting settings

        var adjustedSettings = multiCompletionSession.InputJob.RequestSettings;

        var adjustedSettingsModifier = new SettingsUpdater<CompleteRequestSettings>(adjustedSettings, MultiTextCompletionSettings.CloneRequestSettings);

        bool valueChanged = false;
        if (multiCompletionSession.NamedTextCompletion.MaxTokens != null && adjustedSettings.MaxTokens != null)
        {
            int? ComputeMaxTokens(int? initialValue)
            {
                var newMaxTokens = initialValue;
                if (newMaxTokens != null)
                {
                    switch (multiCompletionSession.NamedTextCompletion.MaxTokensAdjustment)
                    {
                        case MaxTokensAdjustment.Percentage:
                            newMaxTokens = Math.Min(newMaxTokens.Value, multiCompletionSession.NamedTextCompletion.MaxTokens.Value * multiCompletionSession.NamedTextCompletion.MaxTokensReservePercentage / 100);
                            break;
                        case MaxTokensAdjustment.CountInputTokens:
                            if (multiCompletionSession.NamedTextCompletion.TokenCountFunc != null)
                            {
                                newMaxTokens = Math.Min(newMaxTokens.Value, multiCompletionSession.NamedTextCompletion.MaxTokens.Value - multiCompletionSession.NamedTextCompletion.TokenCountFunc(adjustedPrompt));
                            }
                            else
                            {
                                multiCompletionSession.Logger?.LogWarning("Inconsistency found with named Completion {0}: Max Token adjustment is configured to account for input token number but no Token count function was defined. MaxToken settings will be left untouched", multiCompletionSession.NamedTextCompletion.Name);
                            }

                            break;
                    }
                }

                return newMaxTokens;
            }

            adjustedSettings = adjustedSettingsModifier.ModifyIfChanged(r => r.MaxTokens, ComputeMaxTokens, (setting, value) => setting.MaxTokens = value, out valueChanged);

            if (valueChanged)
            {
                multiCompletionSession.Logger?.LogDebug("Changed request max token from {0} to {1}", multiCompletionSession.InputJob.RequestSettings.MaxTokens?.ToString(CultureInfo.InvariantCulture) ?? "null", adjustedSettings.MaxTokens?.ToString(CultureInfo.InvariantCulture) ?? "null");
            }
        }

        if (multiCompletionSession.NamedTextCompletion.TemperatureTransform != null)
        {
            adjustedSettings = adjustedSettingsModifier.ModifyIfChanged(r => r.Temperature, multiCompletionSession.NamedTextCompletion.TemperatureTransform, (setting, value) => setting.Temperature = value, out valueChanged);

            if (valueChanged)
            {
                multiCompletionSession.Logger?.LogDebug("Changed temperature from {0} to {1}", multiCompletionSession.InputJob.RequestSettings.Temperature, adjustedSettings.Temperature);
            }
        }

        if (multiCompletionSession.NamedTextCompletion.RequestSettingsTransform != null)
        {
            adjustedSettings = multiCompletionSession.NamedTextCompletion.RequestSettingsTransform(adjustedSettings);
            multiCompletionSession.Logger?.LogTrace("Applied request settings transform");
        }

        return new CompletionJob(adjustedPrompt, adjustedSettings);
    }
}
