// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Resources;

namespace SemanticKernel.Functions.UnitTests.Grpc.Protobuf.TestPlugins;

internal static class ResourcePluginsProvider
{
    /// <summary>
    /// Loads .proto file from assembly resource.
    /// </summary>
    /// <param name="resourceName">The resource name.</param>
    /// <returns>The OpenAPI document resource stream.</returns>
    public static Stream LoadFromResource(string resourceName)
    {
        var type = typeof(ResourcePluginsProvider);

        return type.Assembly.GetManifestResourceStream(type, resourceName) ??
            throw new MissingManifestResourceException($"Unable to load gRPC plugin from assembly resource '{resourceName}'.");
    }
}
