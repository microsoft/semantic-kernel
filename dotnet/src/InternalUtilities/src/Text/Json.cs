// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;

namespace Microsoft.SemanticKernel.Text;

internal static class Json
{
    internal static string Serialize(object? o) => JsonSerializer.Serialize(o, s_options);

    internal static byte[] SerializeToUtf8Bytes(object? o) => JsonSerializer.SerializeToUtf8Bytes(o, s_options);

    internal static T? Deserialize<T>(string json) => JsonSerializer.Deserialize<T>(json, s_options);

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
