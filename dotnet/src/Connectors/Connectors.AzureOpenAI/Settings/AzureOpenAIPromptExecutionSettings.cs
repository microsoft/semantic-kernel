// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Azure.AI.OpenAI.Chat;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Execution settings for an AzureOpenAI completion request.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class AzureOpenAIPromptExecutionSettings : OpenAIPromptExecutionSettings
{
    /// <summary>
    /// An abstraction of additional settings for chat completion, see https://learn.microsoft.com/en-us/dotnet/api/azure.ai.openai.azurechatextensionsoptions.
    /// This property is compatible only with Azure OpenAI.
    /// </summary>
    [Experimental("SKEXP0010")]
    [JsonIgnore]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public AzureChatDataSource? AzureChatDataSource
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    public AzureChatDataSource? AzureChatDataSource
=======
    public AzureSearchChatDataSource? AzureChatDataSource
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    public AzureSearchChatDataSource? AzureChatDataSource
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    {
        get => this._azureChatDataSource;

        set
        {
            this.ThrowIfFrozen();
            this._azureChatDataSource = value;
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        var settings = base.Clone<AzureOpenAIPromptExecutionSettings>();
        settings.AzureChatDataSource = this.AzureChatDataSource;
        return settings;
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <param name="defaultMaxTokens">Default max tokens</param>
    /// <returns>An instance of OpenAIPromptExecutionSettings</returns>
    public static new AzureOpenAIPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
    {
        if (executionSettings is null)
        {
            return new AzureOpenAIPromptExecutionSettings()
            {
                MaxTokens = defaultMaxTokens
            };
        }

        if (executionSettings is AzureOpenAIPromptExecutionSettings settings)
        {
            return settings;
        }

        if (executionSettings is OpenAIPromptExecutionSettings openAISettings)
        {
            return openAISettings.Clone<AzureOpenAIPromptExecutionSettings>();
        }

        // Having the object as the type of the value to serialize is important to ensure all properties of the settings are serialized.
        // Otherwise, only the properties ServiceId and ModelId from the public API of the PromptExecutionSettings class will be serialized.
        var json = JsonSerializer.Serialize<object>(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<AzureOpenAIPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        // Restore the function choice behavior that lost internal state(list of function instances) during serialization/deserialization process.
        openAIExecutionSettings!.FunctionChoiceBehavior = executionSettings.FunctionChoiceBehavior;

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        // Restore the function choice behavior that lost internal state(list of function instances) during serialization/deserialization process.
        openAIExecutionSettings!.FunctionChoiceBehavior = executionSettings.FunctionChoiceBehavior;

=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        // Restore the function choice behavior that lost internal state(list of function instances) during serialization/deserialization process.
        openAIExecutionSettings!.FunctionChoiceBehavior = executionSettings.FunctionChoiceBehavior;

=======
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        return openAIExecutionSettings!;
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <param name="defaultMaxTokens">Default max tokens</param>
    /// <returns>An instance of OpenAIPromptExecutionSettings</returns>
    [Obsolete("This method is deprecated in favor of OpenAIPromptExecutionSettings.AzureChatExtensionsOptions")]
    public static AzureOpenAIPromptExecutionSettings FromExecutionSettingsWithData(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
    {
        var settings = FromExecutionSettings(executionSettings, defaultMaxTokens);

        if (settings.StopSequences?.Count == 0)
        {
            // Azure OpenAI WithData API does not allow to send empty array of stop sequences
            // Gives back "Validation error at #/stop/str: Input should be a valid string\nValidation error at #/stop/list[str]: List should have at least 1 item after validation, not 0"
            settings.StopSequences = null;
        }

        return settings;
    }

    #region private ================================================================================
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    private AzureChatDataSource? _azureChatDataSource;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes

    private AzureChatDataSource? _azureChatDataSource;
=======
    [Experimental("SKEXP0010")]
    private AzureSearchChatDataSource? _azureChatDataSource;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    [Experimental("SKEXP0010")]
    private AzureSearchChatDataSource? _azureChatDataSource;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

    #endregion
}
