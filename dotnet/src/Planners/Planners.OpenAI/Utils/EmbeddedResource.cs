// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;

namespace Microsoft.SemanticKernel.Planning;

internal static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    internal static string Read(string name)
    {
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly ??
            throw new FileNotFoundException($"[{s_namespace}] {name} assembly not found");

        using Stream? resource = assembly.GetManifestResourceStream($"{s_namespace}." + name) ??
            throw new FileNotFoundException($"[{s_namespace}] {name} resource not found");

        using var reader = new StreamReader(resource);
        return reader.ReadToEnd();
    }
}
