// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Web;

namespace Microsoft.SemanticKernel.Text;

internal static class Json
{
    internal static string Serialize(object? o) => JsonSerializer.Serialize(o, s_options);

    internal static T? Deserialize<T>(string json) => JsonSerializer.Deserialize<T>(json, s_options);

    internal static string ToJson(this object o) => JsonSerializer.Serialize(o, s_options);

    internal static string Encode(string s, bool addQuotes) => addQuotes ? $"\"{HttpUtility.JavaScriptStringEncode(s)}\"" : HttpUtility.JavaScriptStringEncode(s);

    #region private ================================================================================

    private static readonly JsonSerializerOptions s_options = CreateOptions();

    private static JsonSerializerOptions CreateOptions()
    {
        JsonSerializerOptions options = new()
        {
            WriteIndented = true,
            MaxDepth = 20,
            AllowTrailingCommas = true,
            PropertyNameCaseInsensitive = true,
            ReadCommentHandling = JsonCommentHandling.Skip,
        };

        options.Converters.Add(new ReadOnlyMemoryConverter());

        return options;
    }

    #endregion
}
