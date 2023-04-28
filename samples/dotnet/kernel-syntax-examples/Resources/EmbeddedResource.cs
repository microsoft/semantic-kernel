// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using RepoUtils;

namespace Resources;

internal static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    internal static string Read(string name)
    {
        var assembly = typeof(EmbeddedResource).GetTypeInfo().Assembly;
        if (assembly == null) { throw new ConfigurationException($"[{s_namespace}] {name} assembly not found"); }

        var resourceName = $"{s_namespace}." + name;
        // var resourceName = name;
        using Stream? resource = assembly.GetManifestResourceStream(resourceName);
        if (resource == null) { throw new ConfigurationException($"{resourceName} resource not found"); }

        using var reader = new StreamReader(resource);
        return reader.ReadToEnd();
    }
}
