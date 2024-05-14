// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using YamlDotNet.Core;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Allows custom deserialization for derivatives of <see cref="FunctionChoiceBehavior"/>.
/// </summary>
internal sealed class FunctionChoiceBehaviorTypesConverter : IYamlTypeConverter
{
    private const char PromptFunctionNameSeparator = '.';

    private const char FunctionNameSeparator = '-';

    private static IDeserializer? s_deserializer;

    /// <inheritdoc/>
    public bool Accepts(Type type)
    {
#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        return
            type == typeof(AutoFunctionChoiceBehavior) ||
            type == typeof(RequiredFunctionChoiceBehavior) ||
            type == typeof(NoneFunctionChoiceBehavior);
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    }

    public object? ReadYaml(IParser parser, Type type)
    {
        s_deserializer ??= new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .IgnoreUnmatchedProperties() // Required to ignore the 'type' property used as type discrimination. Otherwise, the "Property 'type' not found on type '{type.FullName}'" exception is thrown.
            .Build();

#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        if (type == typeof(AutoFunctionChoiceBehavior))
        {
            var behavior = s_deserializer.Deserialize<AutoFunctionChoiceBehavior>(parser);
            behavior.Functions = ConvertFunctionNames(behavior.Functions);
            return behavior;
        }
        else if (type == typeof(RequiredFunctionChoiceBehavior))
        {
            var behavior = s_deserializer.Deserialize<RequiredFunctionChoiceBehavior>(parser);
            behavior.Functions = ConvertFunctionNames(behavior.Functions);
            return behavior;
        }
        else if (type == typeof(NoneFunctionChoiceBehavior))
        {
            return s_deserializer.Deserialize<NoneFunctionChoiceBehavior>(parser);
        }

        throw new YamlException($"Unexpected type '{type.FullName}' for function choice behavior.");
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    }

    /// <inheritdoc/>
    public void WriteYaml(IEmitter emitter, object? value, Type type)
    {
        throw new NotImplementedException();
    }

    private static IList<string>? ConvertFunctionNames(IList<string>? functions)
    {
        if (functions is null)
        {
            return functions;
        }

        return functions.Select(fqn =>
        {
            var functionName = fqn ?? throw new YamlException("Expected a non-null YAML string.");
            return functionName.Replace(PromptFunctionNameSeparator, FunctionNameSeparator);
        }).ToList();
    }
}
