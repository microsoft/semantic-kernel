// Copyright (c) Microsoft. All rights reserved.

/* Unmerged change from project 'Connectors.OpenAI(netstandard2.0)'
Before:
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
After:
using System.Text.Json.Serialization;
*/

/* Unmerged change from project 'Connectors.OpenAI(netstandard2.0)'
Removed:
using System.Threading.Tasks;
*/
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
