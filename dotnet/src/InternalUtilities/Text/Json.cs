// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;

namespace Microsoft.SemanticKernel.Text;

internal static class Json
{
    internal static readonly JsonSerializerOptions GeneralOptions = new()
    {
        WriteIndented = true,
        MaxDepth = 20,
        AllowTrailingCommas = true,
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
    };
}
