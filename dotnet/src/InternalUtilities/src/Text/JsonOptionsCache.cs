// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Text;

/// <summary>Caches common configurations of <see cref="JsonSerializerOptions"/>.</summary>\
/// <remarks>
/// All of the instances include a converter for <see cref="ReadOnlyMemory{T}"/>.
/// Once the System.Text.Json package is upgraded to 8.0+, this will no longer be
/// necessary and the actual default can be used.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static class JsonOptionsCache
{
    /// <summary>
    /// Cached <see cref="JsonSerializerOptions"/> instance for reading and writing JSON using the default settings.
    /// </summary>
    public static JsonSerializerOptions Default { get; } = new();

    /// <summary>
    /// Cached <see cref="JsonSerializerOptions"/> instance for writing JSON with indentation.
    /// </summary>
    public static JsonSerializerOptions WriteIndented { get; } = new()
    {
        WriteIndented = true,
    };

    /// <summary>
    /// Cached <see cref="JsonSerializerOptions"/> instance for reading JSON in a permissive way,
    /// including support for trailing commas, case-insensitive property names, and comments.
    /// </summary>
    public static JsonSerializerOptions ReadPermissive { get; } = new()
    {
        AllowTrailingCommas = true,
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
    };

    /// <summary>
    /// Gets the <see cref="JsonSerializerOptions"/> configured for serializing chat history data.
    /// </summary>
    public static JsonSerializerOptions ChatHistory { get; } = new()
    {
        Converters = { new ExceptionJsonConverter() }
    };
}
