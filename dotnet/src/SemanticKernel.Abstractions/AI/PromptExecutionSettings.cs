// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides execution settings for an AI request.
/// </summary>
/// <remarks>
/// Implementors of <see cref="ITextGenerationService"/> or <see cref="IChatCompletionService"/> can extend this
/// if the service they are calling supports additional properties. For an example, please reference
/// the Microsoft.SemanticKernel.Connectors.OpenAI.OpenAIPromptExecutionSettings implementation.
/// </remarks>
public class PromptExecutionSettings
{
    /// <summary>
    /// Gets the default service identifier.
    /// </summary>
    /// <remarks>
    /// In a dictionary of <see cref="PromptExecutionSettings"/>, this is the key that should be used settings considered the default.
    /// </remarks>
    public static string DefaultServiceId => "default";

    /// <summary>
    /// Service identifier.
    /// This identifies the service these settings are configured for e.g., azure_openai_eastus, openai, ollama, huggingface, etc.
    /// </summary>
    /// <remarks>
    /// When provided, this service identifier will be the key in a dictionary collection of execution settings for both <see cref="KernelArguments"/> and <see cref="PromptTemplateConfig"/>.
    /// If not provided the service identifier will be the default value in <see cref="DefaultServiceId"/>.
    /// </remarks>
    [JsonPropertyName("service_id")]
    public string? ServiceId
    {
        get => this._serviceId;

        set
        {
            this.ThrowIfFrozen();
            this._serviceId = value;
        }
    }

    /// <summary>
    /// Model identifier.
    /// This identifies the AI model these settings are configured for e.g., gpt-4, gpt-3.5-turbo
    /// </summary>
    [JsonPropertyName("model_id")]
    public string? ModelId
    {
        get => this._modelId;

        set
        {
            this.ThrowIfFrozen();
            this._modelId = value;
        }
    }

    /// <summary>
    /// Gets or sets the behavior defining the way functions are chosen by LLM and how they are invoked by AI connectors.
    /// </summary>
    /// <remarks>
    /// <list type="bullet">
    /// <item>To disable function calling, and have the model only generate a user-facing message, set the property to null (the default).</item>
    /// <item>
    /// To allow the model to decide whether to call the functions and, if so, which ones to call, set the property to an instance returned
    /// by the <see cref="FunctionChoiceBehavior.Auto(IEnumerable{KernelFunction}?, bool, FunctionChoiceBehaviorOptions?)"/> method.
    /// </item>
    /// <item>
    /// To force the model to always call one or more functions set the property to an instance returned
    /// by the <see cref="FunctionChoiceBehavior.Required(IEnumerable{KernelFunction}?, bool, FunctionChoiceBehaviorOptions?)"/> method.
    /// </item>
    /// <item>
    /// To instruct the model to not call any functions and only generate a user-facing message, set the property to an instance returned
    /// by the <see cref="FunctionChoiceBehavior.None(IEnumerable{KernelFunction}?, FunctionChoiceBehaviorOptions?)"/> method.
    /// </item>
    /// </list>
    /// For all the behaviors that presume the model to call functions, auto-invoke can be specified. If LLM
    /// call a function and auto-invoke enabled, SK will attempt to resolve that function from the functions
    /// available, and if found, rather than returning the response back to the caller, it will invoke the function automatically.
    /// The intermediate messages will be retained in the provided <see cref="ChatHistory"/>.
    /// </remarks>
    [JsonPropertyName("function_choice_behavior")]
    public FunctionChoiceBehavior? FunctionChoiceBehavior
    {
        get => this._functionChoiceBehavior;

        set
        {
            this.ThrowIfFrozen();
            this._functionChoiceBehavior = value;
        }
    }

    /// <summary>
    /// Extra properties that may be included in the serialized execution settings.
    /// </summary>
    /// <remarks>
    /// Avoid using this property if possible. Instead, use one of the classes that extends <see cref="PromptExecutionSettings"/>.
    /// </remarks>
    [JsonExtensionData]
    public IDictionary<string, object>? ExtensionData
    {
        get => this._extensionData;

        set
        {
            this.ThrowIfFrozen();
            this._extensionData = value;
        }
    }

    /// <summary>
    /// Gets a value that indicates whether the <see cref="PromptExecutionSettings"/> are currently modifiable.
    /// </summary>
    [JsonIgnore]
    public bool IsFrozen { get; private set; }

    /// <summary>
    /// Makes the current <see cref="PromptExecutionSettings"/> unmodifiable and sets its IsFrozen property to true.
    /// </summary>
    public virtual void Freeze()
    {
        if (this.IsFrozen)
        {
            return;
        }

        this.IsFrozen = true;

        if (this._extensionData is not null)
        {
            this._extensionData = new ReadOnlyDictionary<string, object>(this._extensionData);
        }
    }

    /// <summary>
    /// Creates a new <see cref="PromptExecutionSettings"/> object that is a copy of the current instance.
    /// </summary>
    public virtual PromptExecutionSettings Clone()
    {
        return new()
        {
            ModelId = this.ModelId,
            ServiceId = this.ServiceId,
            FunctionChoiceBehavior = this.FunctionChoiceBehavior,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null
        };
    }

    /// <summary>
    /// Throws an <see cref="InvalidOperationException"/> if the <see cref="PromptExecutionSettings"/> are frozen.
    /// </summary>
    /// <exception cref="InvalidOperationException"></exception>
    protected void ThrowIfFrozen()
    {
        if (this.IsFrozen)
        {
            throw new InvalidOperationException("PromptExecutionSettings are frozen and cannot be modified.");
        }
    }

    #region private ================================================================================

    private string? _modelId;
    private IDictionary<string, object>? _extensionData;
    private string? _serviceId;
    private FunctionChoiceBehavior? _functionChoiceBehavior;

    #endregion
}
