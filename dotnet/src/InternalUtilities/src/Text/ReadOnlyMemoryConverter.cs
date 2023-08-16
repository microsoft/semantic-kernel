// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

// .NET 8 and the System.Text.Json v8.0.0 nuget package include built-in support for ReadOnlyMemory.
// This is a temporary workaround for .NET 6 and the System.Text.Json v6.0.0 nuget package.
// It should be removed once SK projects upgrade to System.Text.Json v8.0.0.

/// <summary>Provides a converter for <see cref="ReadOnlyMemory{Single}"/>.</summary>
internal sealed class ReadOnlyMemoryConverter : JsonConverter<ReadOnlyMemory<float>>
{
    /// <summary>An instance of a converter for float[] that all operations delegate to.</summary>
    private static readonly JsonConverter<float[]> s_arrayConverter = (JsonConverter<float[]>)new JsonSerializerOptions().GetConverter(typeof(float[]));

    public override ReadOnlyMemory<float> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
        s_arrayConverter.Read(ref reader, typeof(float[]), options).AsMemory();

    public override void Write(Utf8JsonWriter writer, ReadOnlyMemory<float> value, JsonSerializerOptions options) =>
        // This provides an efficient implementation when the ReadOnlyMemory represents the full length of an array.
        // This is the common case for these projects, and thus the implementation doesn't spend more code on a complex
        // implementation to efficiently handle slices or instances backed by MemoryManagers.
        s_arrayConverter.Write(
            writer,
            MemoryMarshal.TryGetArray(value, out ArraySegment<float> array) && array.Count == value.Length ? array.Array! : value.ToArray(),
            options);
}
