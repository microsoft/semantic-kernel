// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Extensions;

internal static class ObjectExtensions
{
    private static readonly JsonSerializerOptions s_jsonOptionsCache = new() { WriteIndented = true };

    /// <summary>
    /// Translate an object to a JSON string with identation.
    /// </summary>
    public static string AsJson(this object obj)
    {
        return JsonSerializer.Serialize(obj, s_jsonOptionsCache);
    }
}
