// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;

namespace Microsoft.SemanticKernel.Text;

public static class JsonExtensions
{
    public static string Serialize(object? o)
    {
        return JsonSerializer.Serialize(o, s_options);
    }

    public static T? Deserialize<T>(string json)
    {
        return JsonSerializer.Deserialize<T>(json, s_options);
    }

    public static string ToJson(this object o)
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
