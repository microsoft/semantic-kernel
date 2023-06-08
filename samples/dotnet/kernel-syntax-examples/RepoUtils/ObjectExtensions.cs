// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;

namespace RepoUtils;
public static class ObjectExtensions
{
    private static readonly JsonSerializerOptions s_jsonOptions = new() { WriteIndented = true };

    public static string AsJson(this object obj)
    {
        return JsonSerializer.Serialize(obj, s_jsonOptions);
    }
}
