// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using YamlDotNet.Core;
using YamlDotNet.Core.Events;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.BufferedDeserialization;
using YamlDotNet.Serialization.NamingConventions;
using YamlDotNet.Serialization.ObjectFactories;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Allows custom deserialization for <see cref="PromptExecutionSettings"/> from YAML prompts.
/// </summary>
internal sealed class PromptExecutionSettingsTypeConverter : IYamlTypeConverter
{
    /// <inheritdoc/>
    public bool Accepts(Type type)
    {
        return type == typeof(PromptExecutionSettings);
    }

    /// <inheritdoc/>
    public object? ReadYaml(IParser parser, Type type)
    {
        s_deserializer ??= new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .IgnoreUnmatchedProperties() // Required to ignore the 'type' property used as type discrimination. Otherwise, the "Property 'type' not found on type '{type.FullName}'" exception is thrown.
            .WithObjectFactory(new FunctionChoiceBehaviorsObjectFactory())
            .WithTypeDiscriminatingNodeDeserializer(CreateAndRegisterTypeDiscriminatingNodeDeserializer)
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

    /// <inheritdoc/>
    public void WriteYaml(IEmitter emitter, object? value, Type type)
    {
        throw new NotImplementedException();
    }

    /// <summary>
    /// Creates and register a <see cref="TypeDiscriminatingNodeDeserializer" /> for polymorphic deserialization of <see cref="FunctionChoiceBehavior" />.
    /// </summary>
    /// <param name="options">The <see cref="ITypeDiscriminatingNodeDeserializerOptions" /> to configure the <see cref="TypeDiscriminatingNodeDeserializer" />.</param>
    private static void CreateAndRegisterTypeDiscriminatingNodeDeserializer(ITypeDiscriminatingNodeDeserializerOptions options)
    {
        var attributes = typeof(FunctionChoiceBehavior).GetCustomAttributes(false);

        // Getting the type discriminator property name - "type" from the JsonPolymorphicAttribute.
        var discriminatorKey = attributes.OfType<JsonPolymorphicAttribute>().Single().TypeDiscriminatorPropertyName;
        if (string.IsNullOrEmpty(discriminatorKey))
        {
            throw new InvalidOperationException("Type discriminator property name is not specified.");
        }

        var discriminatorTypeMapping = new Dictionary<string, Type>();

        // Getting FunctionChoiceBehavior subtypes and their type discriminators registered for polymorphic deserialization.
        var derivedTypeAttributes = attributes.OfType<JsonDerivedTypeAttribute>();
        foreach (var derivedTypeAttribute in derivedTypeAttributes)
        {
            var discriminator = derivedTypeAttribute.TypeDiscriminator?.ToString();
            if (string.IsNullOrEmpty(discriminator))
            {
                throw new InvalidOperationException($"Type discriminator is not specified for the {derivedTypeAttribute.DerivedType} type.");
            }

            discriminatorTypeMapping.Add(discriminator!, derivedTypeAttribute.DerivedType);
        }

        options.AddKeyValueTypeDiscriminator<FunctionChoiceBehavior>(discriminatorKey!, discriminatorTypeMapping);
    }

    /// <summary>
    /// The YamlDotNet deserializer instance.
    /// </summary>
    private static IDeserializer? s_deserializer;

    private sealed class FunctionChoiceBehaviorsObjectFactory : ObjectFactoryBase
    {
        private static DefaultObjectFactory? s_defaultFactory = null;

        public override object Create(Type type)
        {
            if (type == typeof(AutoFunctionChoiceBehavior) ||
                type == typeof(NoneFunctionChoiceBehavior) ||
                type == typeof(RequiredFunctionChoiceBehavior))
            {
                return Activator.CreateInstance(type, nonPublic: true)!;
            }

            // Use the default object factory for other types
            return (s_defaultFactory ??= new DefaultObjectFactory()).Create(type);
        }
    }
}
