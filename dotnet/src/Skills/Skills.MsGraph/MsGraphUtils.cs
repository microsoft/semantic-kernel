// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Skills.MsGraph;

internal static class MsGraphUtils
{
    internal static JsonSerializerOptions DefaultSerializerOptions => new()
    {
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };
}
