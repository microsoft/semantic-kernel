// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;
using Microsoft.SemanticKernel.Functions;

namespace Microsoft.SemanticKernel;

[JsonSourceGenerationOptions(JsonSerializerDefaults.Web,
    UseStringEnumConverter = true,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    WriteIndented = true)]
[JsonSerializable(typeof(IDictionary<string, object?>))]
[JsonSerializable(typeof(JsonElement))]
[JsonSerializable(typeof(KernelFunctionSchemaModel))]
[JsonSerializable(typeof(PromptExecutionSettings))]
[JsonSerializable(typeof(KernelArguments))]
// types commonly used as values in settings dictionaries
[JsonSerializable(typeof(string))]
[JsonSerializable(typeof(int))]
[JsonSerializable(typeof(long))]
[JsonSerializable(typeof(float))]
[JsonSerializable(typeof(double))]
[JsonSerializable(typeof(bool))]
[JsonSerializable(typeof(IList<string>))]
internal sealed partial class AbstractionsJsonContext : JsonSerializerContext
{
    /// <summary>Gets the <see cref="JsonSerializerOptions"/> singleton used as the default in JSON serialization operations.</summary>
    private static readonly JsonSerializerOptions s_defaultToolJsonOptions = CreateDefaultToolJsonOptions();

    /// <summary>Gets JSON type information for the specified type.</summary>
    /// <remarks>
    /// This first tries to get the type information from <paramref name="firstOptions"/>,
    /// falling back to <see cref="s_defaultToolJsonOptions"/> if it can't.
    /// </remarks>
    public static JsonTypeInfo GetTypeInfo(Type type, JsonSerializerOptions? firstOptions)
    {
        return firstOptions?.TryGetTypeInfo(type, out JsonTypeInfo? info) is true ?
            info :
            s_defaultToolJsonOptions.GetTypeInfo(type);
    }

    /// <summary>Gets JSON type information for the specified type.</summary>
    /// <remarks>
    /// This first tries to get the type information from <paramref name="firstOptions"/>,
    /// falling back to <see cref="s_defaultToolJsonOptions"/> if it can't.
    /// </remarks>
    public static bool TryGetTypeInfo(Type type, JsonSerializerOptions? firstOptions, [NotNullWhen(true)] out JsonTypeInfo? jsonTypeInfo)
    {
        if (firstOptions?.TryGetTypeInfo(type, out jsonTypeInfo) is true)
        {
            return true;
        }

        return s_defaultToolJsonOptions.TryGetTypeInfo(type, out jsonTypeInfo);
    }

    /// <summary>Creates the default <see cref="JsonSerializerOptions"/> to use for serialization-related operations.</summary>
    [UnconditionalSuppressMessage("AotAnalysis", "IL3050", Justification = "DefaultJsonTypeInfoResolver is only used when reflection-based serialization is enabled")]
    [UnconditionalSuppressMessage("ReflectionAnalysis", "IL2026", Justification = "DefaultJsonTypeInfoResolver is only used when reflection-based serialization is enabled")]
    private static JsonSerializerOptions CreateDefaultToolJsonOptions()
    {
        // If reflection-based serialization is enabled by default, use it, as it's the most permissive in terms of what it can serialize,
        // and we want to be flexible in terms of what can be put into the various collections in the object model.
        // Otherwise, use the source-generated options to enable trimming and Native AOT.

        if (JsonSerializer.IsReflectionEnabledByDefault)
        {
            // Keep in sync with the JsonSourceGenerationOptions attribute on JsonContext above.
            JsonSerializerOptions options = new(JsonSerializerDefaults.Web)
            {
                TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
                Converters = { new JsonStringEnumConverter() },
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
                WriteIndented = true,
            };

            options.MakeReadOnly();
            return options;
        }

        return Default.Options;
    }
}
