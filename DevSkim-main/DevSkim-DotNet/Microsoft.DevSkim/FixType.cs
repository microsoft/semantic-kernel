// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System.Text.Json.Serialization;
using System;
using System.Text.Json;

namespace Microsoft.DevSkim
{
    /// <summary>
    ///     Code Fix Type
    /// </summary>
    [JsonConverter(typeof(FixTypeConverter))]
    public enum FixType
    {
        Unknown,
        RegexReplace
    }

    /// <summary>
    ///     Json Converter for FixType
    /// </summary>
    internal class FixTypeConverter : JsonConverter<FixType>
    {
        public override FixType Read(
            ref Utf8JsonReader reader,
            Type typeToConvert,
            JsonSerializerOptions options)
        {
            if (reader.GetString() is string value)
            {
                if (Enum.TryParse<FixType>(value.Replace("-", ""), true, out FixType result))
                {
                    return result;
                }
            }
            return 0;
        }

        public override void Write(
            Utf8JsonWriter writer,
            FixType fixTypeValue,
            JsonSerializerOptions options) =>
                writer.WriteStringValue(fixTypeValue.ToString());
    }
}