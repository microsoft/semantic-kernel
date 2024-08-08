// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Text.Json;
using Azure.AI.Inference;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AzureAIInference;

/// <summary>
/// Chat completion execution settings.
/// </summary>
public class AzureAIInferenceChatExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAIInferenceChatExecutionSettings"/> class.
    /// </summary>
    public AzureAIInferenceChatExecutionSettings()
    {
        this.ExtensionData = new Dictionary<string, object>();
    }

    /// <summary>
    /// Allowed values: "error" | "drop" | "pass-through"
    /// </summary>
    public string? ExtraParameters
    {
        get => this.GetValueExtensionData("extra_parameters") as string;
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value!, "extra_parameters");
        }
    }

    /// <summary>
    /// A value that influences the probability of generated tokens appearing based on their cumulative
    /// frequency in generated text.
    /// Positive values will make tokens less likely to appear as their frequency increases and
    /// decrease the likelihood of the model repeating the same statements verbatim.
    /// Supported range is [-2, 2].
    /// </summary>
    public float? FrequencyPenalty
    {
        get => this.GetValueExtensionData("frequency_penalty") as float?;
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value!, "frequency_penalty");
        }
    }

    /// <summary>
    /// A value that influences the probability of generated tokens appearing based on their existing
    /// presence in generated text.
    /// Positive values will make tokens less likely to appear when they already exist and increase the
    /// model's likelihood to output new topics.
    /// Supported range is [-2, 2].
    /// </summary>
    public float? PresencePenalty
    {
        get => this.GetValueExtensionData("presence_penalty") as float?;
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value!, "presence_penalty");
        }
    }

    /// <summary>
    /// The sampling temperature to use that controls the apparent creativity of generated completions.
    /// Higher values will make output more random while lower values will make results more focused
    /// and deterministic.
    /// It is not recommended to modify temperature and top_p for the same completions request as the
    /// interaction of these two settings is difficult to predict.
    /// Supported range is [0, 1].
    /// </summary>
    public float? Temperature
    {
        get => this.GetValueExtensionData("temperature") as float?;
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value!, "temperature");
        }
    }

    /// <summary>
    /// An alternative to sampling with temperature called nucleus sampling. This value causes the
    /// model to consider the results of tokens with the provided probability mass. As an example, a
    /// value of 0.15 will cause only the tokens comprising the top 15% of probability mass to be
    /// considered.
    /// It is not recommended to modify temperature and top_p for the same completions request as the
    /// interaction of these two settings is difficult to predict.
    /// Supported range is [0, 1].
    /// </summary>
    public float? NucleusSamplingFactor
    {
        get => this.GetValueExtensionData("top_p") as float?;
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value!, "top_p");
        }
    }

    /// <summary> The maximum number of tokens to generate. </summary>
    public int? MaxTokens
    {
        get => this.GetValueExtensionData("max_tokens") as int?;
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value!, "max_tokens");
        }
    }

    /// <summary>
    /// The format that the model must output. Use this to enable JSON mode instead of the default text mode.
    /// Note that to enable JSON mode, some AI models may also require you to instruct the model to produce JSON
    /// via a system or user message.
    /// Please note <see cref="ChatCompletionsResponseFormat"/> is the base class. According to the scenario, a derived class of the base class might need to be assigned here, or this property needs to be casted to one of the possible derived classes.
    /// The available derived classes include <see cref="ChatCompletionsResponseFormatJSON"/> and <see cref="ChatCompletionsResponseFormatText"/>.
    /// </summary>
    public object? ResponseFormat
    {
        get => this.GetValueExtensionData("response_format");
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value!, "response_format");
        }
    }

    /// <summary> A collection of textual sequences that will end completions generation. </summary>
    public IList<string> StopSequences
    {
        get => (this.GetValueExtensionData("stop") as IList<string>) ?? [];
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value, "stop");
        }
    }

    /// <summary>
    /// The available tool definitions that the chat completions request can use, including caller-defined functions.
    /// Please note <see cref="ChatCompletionsToolDefinition"/> is the base class. According to the scenario, a derived class of the base class might need to be assigned here, or this property needs to be casted to one of the possible derived classes.
    /// The available derived classes include <see cref="ChatCompletionsFunctionToolDefinition"/>.
    /// </summary>
    public IList<ChatCompletionsToolDefinition> Tools
    {
        get => (this.GetValueExtensionData("tools") as IList<ChatCompletionsToolDefinition>) ?? [];
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value, "tools");
        }
    }

    /// <summary>
    /// If specified, the system will make a best effort to sample deterministically such that repeated requests with the
    /// same seed and parameters should return the same result. Determinism is not guaranteed.
    /// </summary>
    public long? Seed
    {
        get => this.GetValueExtensionData("seed") as long?;
        set
        {
            this.ThrowIfFrozen();
            this.SetValueInExtensionData(value!, "seed");
        }
    }

    /// <inheritdoc/>
    public override void Freeze()
    {
        if (this.IsFrozen)
        {
            return;
        }

        base.Freeze();

        this.ExtensionData = new ReadOnlyDictionary<string, object>(this.ExtensionData!);
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new AzureAIInferenceChatExecutionSettings()
        {
            // As all the properties retrieve values from the extension data, we can just clone the extension data.
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
        };
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <param name="defaultMaxTokens">Default max tokens</param>
    /// <returns>An instance of <see cref="AzureAIInferenceChatExecutionSettings"/></returns>
    public static AzureAIInferenceChatExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
    {
        if (executionSettings is null)
        {
            return new AzureAIInferenceChatExecutionSettings();
        }

        if (executionSettings is AzureAIInferenceChatExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var aiInferenceSettings = JsonSerializer.Deserialize<AzureAIInferenceChatExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        if (aiInferenceSettings is not null)
        {
            return aiInferenceSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(AzureAIInferenceChatExecutionSettings)}", nameof(executionSettings));
    }

    #region private ================================================================================

    private void SetValueInExtensionData(object value, string propertyName)
        => this.ExtensionData![propertyName] = value;

    private object? GetValueExtensionData(string propertyName)
        => this.ExtensionData!.TryGetValue(propertyName, out var value) ? value : null;

    #endregion
}
