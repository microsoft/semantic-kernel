// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;

namespace MCPServer.ProjectResources;

/// <summary>
/// Reads embedded resources.
/// </summary>
public static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    /// <summary>
    /// Read an embedded resource as a string.
    /// </summary>
    /// <param name="resourcePath">The path to the resource, relative to the assembly namespace.</param>
    /// <returns>A string containing the resource content.</returns>
    public static string ReadAsString(string resourcePath)
    {
        Stream stream = ReadAsStream(resourcePath);

        using StreamReader reader = new(stream);
        return reader.ReadToEnd();
    }

    /// <summary>
    /// Read an embedded resource as a byte array.
    /// </summary>
    /// <param name="resourcePath">The path to the resource, relative to the assembly namespace.</param>
    /// <returns>A byte array containing the resource content.</returns>
    public static byte[] ReadAsBytes(string resourcePath)
    {
        Stream stream = ReadAsStream(resourcePath);

        using MemoryStream memoryStream = new();
        stream.CopyTo(memoryStream);
        return memoryStream.ToArray();
    }

    /// <summary>
    /// Read an embedded resource as a stream.
    /// </summary>
    /// <param name="resourcePath">The path to the resource, relative to the assembly namespace.</param>
    /// <returns>A stream containing the resource content.</returns>
    public static Stream ReadAsStream(string resourcePath)
    {
        // Get the current assembly. Note: this class is in the same assembly where the embedded resources are stored.
        Assembly assembly =
            typeof(EmbeddedResource).GetTypeInfo().Assembly ??
            throw new InvalidOperationException($"[{s_namespace}] {resourcePath} assembly not found");

        // Resources are mapped like types, using the namespace and appending "." (dot) and the file name
        string resourceName = $"{s_namespace}.{resourcePath}";

        return
            assembly.GetManifestResourceStream(resourceName) ??
            throw new InvalidOperationException($"{resourceName} resource not found");
    }
}
