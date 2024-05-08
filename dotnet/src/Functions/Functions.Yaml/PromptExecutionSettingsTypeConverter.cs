// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using YamlDotNet.Core;
using YamlDotNet.Core.Events;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel;

internal sealed class PromptExecutionSettingsTypeConverter : IYamlTypeConverter
{
    private static IDeserializer? s_deserializer;

    public bool Accepts(Type type)
    {
        return type == typeof(PromptExecutionSettings);
    }

    public object? ReadYaml(IParser parser, Type type)
    {
        s_deserializer ??= new DeserializerBuilder()
            .WithNamingConvention(CamelCaseNamingConvention.Instance)
            .IgnoreUnmatchedProperties() // Required to ignore the 'type' property used for type discrimination. Otherwise, the "Property '{name}' not found on type '{type.FullName}'" exception is thrown.
            .WithTypeDiscriminatingNodeDeserializer((options) =>
            {
                options.AddKeyValueTypeDiscriminator<FunctionChoiceBehavior>("type", new Dictionary<string, Type>
                {
                    { "auto", typeof(AutoFunctionChoiceBehavior) },
                    { "required", typeof(RequiredFunctionChoiceBehavior) },
                    { "none", typeof(NoneFunctionChoiceBehavior) }
                });
            })
            .Build();

        parser.MoveNext(); // Move to the first property  

        var executionSettings = new PromptExecutionSettings();
        while (parser.Current is not MappingEnd)
        {
            var propertyName = parser.Consume<Scalar>().Value;
            switch (propertyName)
            {
                case "model_id":
                    executionSettings.ModelId = s_deserializer.Deserialize<string>(parser);
                    break;
                case "function_choice_behavior":
                    executionSettings.FunctionChoiceBehavior = s_deserializer.Deserialize<FunctionChoiceBehavior>(parser);
                    break;
                default:
                    (executionSettings.ExtensionData ??= new Dictionary<string, object>()).Add(propertyName, s_deserializer.Deserialize<object>(parser));
                    break;
            }
        }
        parser.MoveNext(); // Move past the MappingEnd event  
        return executionSettings;
    }

    public void WriteYaml(IEmitter emitter, object? value, Type type)
    {
        throw new NotImplementedException();
    }
}
