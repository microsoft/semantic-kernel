// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel;

/// <summary>Extensions methods for <see cref="PromptExecutionSettings"/>.</summary>
public static class PromptExecutionSettingsExtensions
{
    /// <summary>Converts a pair of <see cref="PromptExecutionSettings"/> and <see cref="Kernel"/> to a <see cref="ChatOptions"/>.</summary>
    public static ChatOptions? ToChatOptions(this PromptExecutionSettings? settings, Kernel? kernel)
    {
        if (settings is null)
        {
            return null;
        }

        if (settings.GetType() != typeof(PromptExecutionSettings))
        {
            var originalFunctionChoiceBehavior = settings.FunctionChoiceBehavior;

            // If the settings are of a derived type, roundtrip through JSON to the base type in order to try
            // to get the derived strongly-typed properties to show up in the loosely-typed ExtensionData dictionary.
            // This has the unfortunate effect of making all the ExtensionData values into JsonElements, so we lose
            // some type fidelity. (As an alternative, we could introduce new interfaces that could be queried for
            // in this method and implemented by the derived settings types to control how they're converted to
            // ChatOptions.)
            settings = JsonSerializer.Deserialize(
                JsonSerializer.Serialize(settings, AbstractionsJsonContext.GetTypeInfo(settings.GetType(), null)),
                AbstractionsJsonContext.Default.PromptExecutionSettings);

            settings!.FunctionChoiceBehavior = originalFunctionChoiceBehavior;
        }

        ChatOptions options = new()
        {
            ModelId = settings.ModelId
        };

        if (settings.ExtensionData is IDictionary<string, object> extensionData)
        {
            foreach (var entry in extensionData)
            {
                if (entry.Key.Equals("temperature", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out float temperature))
                {
                    options.Temperature = temperature;
                }
                else if (entry.Key.Equals("top_p", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out float topP))
                {
                    options.TopP = topP;
                }
                else if (entry.Key.Equals("top_k", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out int topK))
                {
                    options.TopK = topK;
                }
                else if (entry.Key.Equals("seed", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out long seed))
                {
                    options.Seed = seed;
                }
                else if (entry.Key.Equals("max_tokens", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out int maxTokens))
                {
                    options.MaxOutputTokens = maxTokens;
                }
                else if (entry.Key.Equals("frequency_penalty", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out float frequencyPenalty))
                {
                    options.FrequencyPenalty = frequencyPenalty;
                }
                else if (entry.Key.Equals("presence_penalty", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out float presencePenalty))
                {
                    options.PresencePenalty = presencePenalty;
                }
                else if (entry.Key.Equals("stop_sequences", StringComparison.OrdinalIgnoreCase) &&
                    TryConvert(entry.Value, out IList<string>? stopSequences))
                {
                    options.StopSequences = stopSequences;
                }
                else if (entry.Key.Equals("response_format", StringComparison.OrdinalIgnoreCase) &&
                    entry.Value is { } responseFormat)
                {
                    if (TryConvert(responseFormat, out string? responseFormatString))
                    {
                        options.ResponseFormat = responseFormatString switch
                        {
                            "text" => ChatResponseFormat.Text,
                            "json_object" => ChatResponseFormat.Json,
                            _ => null,
                        };
                    }
                    else
                    {
                        options.ResponseFormat = responseFormat is JsonElement e ? ChatResponseFormat.ForJsonSchema(e) : null;
                    }
                }
                else
                {
                    // Roundtripping a derived PromptExecutionSettings through the base type will have put all the
                    // object values in AdditionalProperties into JsonElements. Convert them back where possible.
                    object? value = entry.Value;
                    if (value is JsonElement jsonElement)
                    {
                        value = jsonElement.ValueKind switch
                        {
                            JsonValueKind.String => jsonElement.GetString(),
                            JsonValueKind.Number => jsonElement.GetDouble(), // not perfect, but a reasonable heuristic
                            JsonValueKind.True => true,
                            JsonValueKind.False => false,
                            JsonValueKind.Null => null,
                            _ => value,
                        };

                        if (jsonElement.ValueKind == JsonValueKind.Array)
                        {
                            var enumerator = jsonElement.EnumerateArray();

                            var enumeratorType = enumerator.MoveNext() ? enumerator.Current.ValueKind : JsonValueKind.Null;

                            switch (enumeratorType)
                            {
                                case JsonValueKind.String:
                                    value = enumerator.Select(e => e.GetString());
                                    break;
                                case JsonValueKind.Number:
                                    value = enumerator.Select(e => e.GetDouble());
                                    break;
                                case JsonValueKind.True or JsonValueKind.False:
                                    value = enumerator.Select(e => e.ValueKind == JsonValueKind.True);
                                    break;
                            }
                        }
                    }

                    (options.AdditionalProperties ??= [])[entry.Key] = value;
                }
            }
        }

        if (settings.FunctionChoiceBehavior?.GetConfiguration(new([]) { Kernel = kernel }).Functions is { Count: > 0 } functions)
        {
            if (settings.FunctionChoiceBehavior is AutoFunctionChoiceBehavior autoChoiceBehavior)
            {
                options.ToolMode = ChatToolMode.Auto;
                options.AllowMultipleToolCalls = autoChoiceBehavior.Options?.AllowParallelCalls;
            }
            else
            if (settings.FunctionChoiceBehavior is NoneFunctionChoiceBehavior noneFunctionChoiceBehavior)
            {
                options.ToolMode = ChatToolMode.None;
            }
            else
            if (settings.FunctionChoiceBehavior is RequiredFunctionChoiceBehavior requiredFunctionChoiceBehavior)
            {
                options.ToolMode = ChatToolMode.RequireAny;
                options.AllowMultipleToolCalls = requiredFunctionChoiceBehavior.Options?.AllowParallelCalls;
            }

            options.Tools = [];
            foreach (var function in functions)
            {
                // Clone the function to ensure it works running as a AITool lower-level abstraction for the specified kernel.
                var functionClone = function.WithKernel(kernel);
                options.Tools.Add(functionClone);
            }
        }

        // Enables usage of AutoFunctionInvocationFilters
        return kernel is null
            ? options
            : new KernelChatOptions(kernel, options, settings: settings);

        // Be a little lenient on the types of the values used in the extension data,
        // e.g. allow doubles even when requesting floats.
        static bool TryConvert<T>(object? value, [NotNullWhen(true)] out T? result)
        {
            if (value is not null)
            {
                // If the value is a T, use it.
                if (value is T typedValue)
                {
                    result = typedValue;
                    return true;
                }

                if (value is JsonElement json)
                {
                    // If the value is JsonElement, it likely resulted from JSON serializing as object.
                    // Try to deserialize it as a T. This currently will only be successful either when
                    // reflection-based serialization is enabled or T is one of the types special-cased
                    // in the AbstractionsJsonContext. For other cases with NativeAOT, we would need to
                    // have a JsonSerializationOptions with the relevant type information.
                    if (AbstractionsJsonContext.TryGetTypeInfo(typeof(T), firstOptions: null, out JsonTypeInfo? jti))
                    {
                        try
                        {
                            result = (T)json.Deserialize(jti)!;
                            return true;
                        }
                        catch (Exception e) when (e is ArgumentException or JsonException or NotSupportedException or InvalidOperationException)
                        {
                        }
                    }
                }
                else
                {
                    // Otherwise, try to convert it to a T using Convert, in particular to handle conversions between numeric primitive types.
                    try
                    {
                        result = (T)Convert.ChangeType(value, typeof(T), CultureInfo.InvariantCulture);
                        return true;
                    }
                    catch (Exception e) when (e is ArgumentException or FormatException or InvalidCastException or OverflowException)
                    {
                    }
                }
            }

            result = default;
            return false;
        }
    }
}
