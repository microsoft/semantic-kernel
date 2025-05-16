// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Extensions methods for <see cref="ChatOptions"/>.
/// </summary>
internal static class ChatOptionsExtensions
{
    /// <summary>Converts a <see cref="ChatOptions"/> to a <see cref="PromptExecutionSettings"/>.</summary>
    internal static PromptExecutionSettings? ToPromptExecutionSettings(this ChatOptions? options)
    {
        if (options is null)
        {
            return null;
        }

        PromptExecutionSettings settings = new()
        {
            ExtensionData = new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase),
            ModelId = options.ModelId,
        };

        // Transfer over all strongly-typed members of ChatOptions. We do not know the exact name the derived PromptExecutionSettings
        // will pick for these options, so we just use the most common choice for each. (We could make this more exact by having an
        // IPromptExecutionSettingsFactory interface with a method like `PromptExecutionSettings Create(ChatOptions options)`; that
        // interface could then optionally be implemented by an IChatCompletionService, and this implementation could just ask the
        // chat completion service to produce the PromptExecutionSettings it wants. But, this is already a problem
        // with PromptExecutionSettings, regardless of ChatOptions... someone creating a PES without knowing what backend is being
        // used has to guess at the names to use.)

        if (options.Temperature is not null)
        {
            settings.ExtensionData["temperature"] = options.Temperature.Value;
        }

        if (options.MaxOutputTokens is not null)
        {
            settings.ExtensionData["max_tokens"] = options.MaxOutputTokens.Value;
        }

        if (options.FrequencyPenalty is not null)
        {
            settings.ExtensionData["frequency_penalty"] = options.FrequencyPenalty.Value;
        }

        if (options.PresencePenalty is not null)
        {
            settings.ExtensionData["presence_penalty"] = options.PresencePenalty.Value;
        }

        if (options.StopSequences is not null)
        {
            settings.ExtensionData["stop_sequences"] = options.StopSequences;
        }

        if (options.TopP is not null)
        {
            settings.ExtensionData["top_p"] = options.TopP.Value;
        }

        if (options.TopK is not null)
        {
            settings.ExtensionData["top_k"] = options.TopK.Value;
        }

        if (options.Seed is not null)
        {
            settings.ExtensionData["seed"] = options.Seed.Value;
        }

        if (options.ResponseFormat is not null)
        {
            if (options.ResponseFormat is ChatResponseFormatText)
            {
                settings.ExtensionData["response_format"] = "text";
            }
            else if (options.ResponseFormat is ChatResponseFormatJson json)
            {
                settings.ExtensionData["response_format"] = json.Schema is JsonElement schema ?
                    JsonSerializer.Deserialize(schema, AbstractionsJsonContext.Default.JsonElement) :
                    "json_object";
            }
        }

        // Transfer over loosely-typed members of ChatOptions.

        if (options.AdditionalProperties is not null)
        {
            foreach (var kvp in options.AdditionalProperties)
            {
                if (kvp.Value is not null)
                {
                    settings.ExtensionData[kvp.Key] = kvp.Value;
                }
            }
        }

        // Transfer over tools. For IChatClient, we do not want automatic invocation, as that's a concern left up to
        // components like FunctionInvocationChatClient. As such, based on the tool mode, we map to the appropriate
        // FunctionChoiceBehavior, but always with autoInvoke: false.

        if (options.Tools is { Count: > 0 })
        {
            var functions = options.Tools.OfType<AIFunction>().Select(f => new AIFunctionKernelFunction(f));
            settings.FunctionChoiceBehavior =
                options.ToolMode is null or AutoChatToolMode ? FunctionChoiceBehavior.Auto(functions, autoInvoke: false) :
                options.ToolMode is RequiredChatToolMode { RequiredFunctionName: null } ? FunctionChoiceBehavior.Required(functions, autoInvoke: false) :
                options.ToolMode is RequiredChatToolMode { RequiredFunctionName: string functionName } ? FunctionChoiceBehavior.Required(functions.Where(f => f.Name == functionName), autoInvoke: false) :
                null;
        }

        return settings;
    }
}
