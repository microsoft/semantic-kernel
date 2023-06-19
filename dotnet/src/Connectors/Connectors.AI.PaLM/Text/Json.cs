// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;

namespace Microsoft.SemanticKernel.Text;

internal static class Json
{
    internal static string Serialize(object? o)
    {
        return JsonSerializer.Serialize(o, s_options);
    }

    internal static T? Deserialize<T>(string json)
    {
        return JsonSerializer.Deserialize<T>(json, s_options);
    }

    internal static string ToJson(this object o)
    {
        return JsonSerializer.Serialize(o, s_options);
    }

    #region private ================================================================================

    private static readonly JsonSerializerOptions s_options = new()
    {
        WriteIndented = true,
        MaxDepth = 20,
        AllowTrailingCommas = true,
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
    };

    #endregion
}
