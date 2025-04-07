// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;

namespace MCPServer.Prompts;

/// <summary>
/// Reads embedded resources.
/// </summary>
public static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    internal static string ReadAsString(string fileName)
    {
        // Get the current assembly. Note: this class is in the same assembly where the embedded resources are stored.
        Assembly assembly =
            typeof(EmbeddedResource).GetTypeInfo().Assembly ??
            throw new InvalidOperationException($"[{s_namespace}] {fileName} assembly not found");

        // Resources are mapped like types, using the namespace and appending "." (dot) and the file name
        string resourceName = $"{s_namespace}.{fileName}";

        Stream stream =
            assembly.GetManifestResourceStream(resourceName) ??
            throw new InvalidOperationException($"{resourceName} resource not found");

        // Return the resource content, in text format.
        using StreamReader reader = new(stream);
        return reader.ReadToEnd();
    }
}
