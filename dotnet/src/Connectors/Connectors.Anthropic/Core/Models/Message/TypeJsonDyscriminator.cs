// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

// Temporary solution from https://github.com/dotnet/runtime/issues/72604
// TODO: Remove this once we move to .NET 9

internal static class JsonTypeDiscriminatorHelper
{
    internal static IJsonTypeInfoResolver TypeInfoResolver { get; } = new DefaultJsonTypeInfoResolver
    {
        Modifiers =
        {
            static typeInfo =>
            {
                var propertyNamingPolicy = typeInfo.Options.PropertyNamingPolicy;

                // Temporary hack to ensure subclasses of abstract classes will always include the type field
                if (typeInfo.Type.BaseType is { IsAbstract: true } &&
                    typeInfo.Type.BaseType.GetCustomAttributes<HackyJsonDerivedAttribute>().Any())
                {
                    var discriminatorPropertyName = propertyNamingPolicy?.ConvertName("type") ?? "type";
                    if (typeInfo.Properties.All(p => p.Name != discriminatorPropertyName))
                    {
                        var discriminatorValue = typeInfo.Type.BaseType
                            .GetCustomAttributes<HackyJsonDerivedAttribute>()
                            .First(attr => attr.Subtype == typeInfo.Type).TypeDiscriminator;
                        var propInfo = typeInfo.CreateJsonPropertyInfo(typeof(string), discriminatorPropertyName);
                        propInfo.Get = _ => discriminatorValue;
                        typeInfo.Properties.Insert(0, propInfo);
                    }
                }
            },
        },
    };
}

/// <summary>
/// Same as <see cref="JsonDerivedTypeAttribute"/> but used for the hack below. Necessary because using the built-in
/// attribute will lead to NotSupportedExceptions.
/// </summary>
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Interface, AllowMultiple = true, Inherited = false)]
internal sealed class HackyJsonDerivedAttribute(Type subtype, string typeDiscriminator) : Attribute
{
    public Type Subtype { get; set; } = subtype;
    public string TypeDiscriminator { get; set; } = typeDiscriminator;
}

internal sealed class PolymorphicJsonConverterFactory : JsonConverterFactory
{
    public override bool CanConvert(Type typeToConvert)
    {
        return typeToConvert.IsAbstract && typeToConvert.GetCustomAttributes<HackyJsonDerivedAttribute>().Any();
    }

    public override JsonConverter? CreateConverter(Type typeToConvert, JsonSerializerOptions options)
    {
        return (JsonConverter?)Activator.CreateInstance(
            typeof(PolymorphicJsonConverter<>).MakeGenericType(typeToConvert), options);
    }
}

/// <summary>
/// A temporary hack to support deserializing JSON payloads that use polymorphism but don't specify type as the first field.
/// Modified from https://github.com/dotnet/runtime/issues/72604#issuecomment-1440708052.
/// </summary>
internal sealed class PolymorphicJsonConverter<T> : JsonConverter<T>
{
    private readonly string _discriminatorPropName;
    private readonly Dictionary<string, Type> _discriminatorToSubtype = [];

    public PolymorphicJsonConverter(JsonSerializerOptions options)
    {
        this._discriminatorPropName = options.PropertyNamingPolicy?.ConvertName("type") ?? "type";
        foreach (var subtype in typeof(T).GetCustomAttributes<HackyJsonDerivedAttribute>())
        {
            this._discriminatorToSubtype.Add(subtype.TypeDiscriminator, subtype.Subtype);
        }
    }

    public override bool CanConvert(Type typeToConvert) => typeof(T) == typeToConvert;

    public override T Read(
        ref Utf8JsonReader reader, Type objectType, JsonSerializerOptions options)
    {
        var reader2 = reader;
        using var doc = JsonDocument.ParseValue(ref reader2);

        var root = doc.RootElement;
        var typeField = root.GetProperty(this._discriminatorPropName);

        if (typeField.GetString() is not { } typeName)
        {
            throw new JsonException(
                $"Could not find string property {this._discriminatorPropName} " +
                $"when trying to deserialize {typeof(T).Name}");
        }

        if (!this._discriminatorToSubtype.TryGetValue(typeName, out var type))
        {
            throw new JsonException($"Unknown type: {typeName}");
        }

        return (T)JsonSerializer.Deserialize(ref reader, type, options)!;
    }

    public override void Write(
        Utf8JsonWriter writer, T? value, JsonSerializerOptions options)
    {
        var type = value!.GetType();
        JsonSerializer.Serialize(writer, value, type, options);
    }
}
