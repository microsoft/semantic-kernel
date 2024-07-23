// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

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
        foreach (var subtype in typeof(T).GetCustomAttributes<InternalJsonDerivedAttribute>())
        {
            this._discriminatorToSubtype.Add(subtype.TypeDiscriminator, subtype.Subtype);
        }
    }

    public override bool CanConvert(Type typeToConvert) => typeof(T) == typeToConvert;

    public override T Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
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

    public override void Write(Utf8JsonWriter writer, T? value, JsonSerializerOptions options)
    {
        var type = value!.GetType();
        JsonSerializer.Serialize(writer, value, type, options);
    }
}
