// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Text.Json;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.OpenAI.Core;
/*internal class OpenAITextToImageExecutionSettingsConverter : JsonConverter<OpenAITextToImageExecutionSettings>
{
    public override OpenAITextToImageExecutionSettings Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var settings = base.Read(ref reader, typeToConvert, options);

        // I need to read the width and height properties from the JSON object after the base.Read() call

        return settings;
    }

    public override void Write(Utf8JsonWriter writer, OpenAITextToImageExecutionSettings value, JsonSerializerOptions options)
    {
        base.Write(writer, value, options);
    }
}*/
