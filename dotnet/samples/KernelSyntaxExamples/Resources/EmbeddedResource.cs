// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using RepoUtils;

namespace Resources;

/// <summary>
/// Resource helper to load resources embedded in the assembly. By default we embed only
/// text files, so the helper is limited to returning text.
///
/// You can find information about embedded resources here:
/// * https://learn.microsoft.com/dotnet/core/extensions/create-resource-files
/// * https://learn.microsoft.com/dotnet/api/system.reflection.assembly.getmanifestresourcestream?view=net-7.0
///
/// To know which resources are embedded, check the csproj file.
/// </summary>
internal static class EmbeddedResource
{
    private static readonly string? s_namespace = typeof(EmbeddedResource).Namespace;

    internal static string Read(string fileName)
    {
        // Get the current assembly. Note: this class is in the same assembly where the embedded resources are stored.
        Assembly assembly =
            typeof(EmbeddedResource).GetTypeInfo().Assembly ??
            throw new ConfigurationException($"[{s_namespace}] {fileName} assembly not found");

        // Resources are mapped like types, using the namespace and appending "." (dot) and the file name
        var resourceName = $"{s_namespace}." + fileName;
        using Stream resource =
            assembly.GetManifestResourceStream(resourceName) ??
            throw new ConfigurationException($"{resourceName} resource not found");

        // Return the resource content, in text format.
        using var reader = new StreamReader(resource);
        return reader.ReadToEnd();
    }

    internal static Stream? ReadStream(string fileName)
    {
        // Get the current assembly. Note: this class is in the same assembly where the embedded resources are stored.
        Assembly assembly =
            typeof(EmbeddedResource).GetTypeInfo().Assembly ??
            throw new ConfigurationException($"[{s_namespace}] {fileName} assembly not found");

        // Resources are mapped like types, using the namespace and appending "." (dot) and the file name
        var resourceName = $"{s_namespace}." + fileName;
        return assembly.GetManifestResourceStream(resourceName);
    }

    internal async static Task<ReadOnlyMemory<byte>> ReadAllAsync(string fileName)
    {
        await using Stream? resourceStream = ReadStream(fileName);
        using var memoryStream = new MemoryStream();

        // Copy the resource stream to the memory stream
        await resourceStream!.CopyToAsync(memoryStream);

        // Convert the memory stream's buffer to ReadOnlyMemory<byte>
        // Note: ToArray() creates a copy of the buffer, which is fine for converting to ReadOnlyMemory<byte>
        return new ReadOnlyMemory<byte>(memoryStream.ToArray());
    }
}
