// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.SemanticFunctions;

internal class RequestSettingsConverter : JsonConverter<dynamic>
{
    public override dynamic Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var element = JsonSerializer.Deserialize<JsonElement>(ref reader, options);
        return element.ToExpando();
    }

    public override void Write(Utf8JsonWriter writer, dynamic value, JsonSerializerOptions options)
    {
        // Write the anonymous type as a regular object
        JsonSerializer.Serialize(writer, value, value.GetType(), options);
    }
}
