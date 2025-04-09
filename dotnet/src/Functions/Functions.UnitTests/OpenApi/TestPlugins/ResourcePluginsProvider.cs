// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Resources;

namespace SemanticKernel.Functions.UnitTests.OpenApi.TestPlugins;

internal static class ResourcePluginsProvider
{
    /// <summary>
    /// Loads OpenAPI document from assembly resource.
    /// </summary>
    /// <param name="resourceName">The resource name.</param>
    /// <returns>The OpenAPI document resource stream.</returns>
    public static Stream LoadFromResource(string resourceName)
    {
        var type = typeof(ResourcePluginsProvider);

        return type.Assembly.GetManifestResourceStream(type, resourceName) ??
            throw new MissingManifestResourceException($"Unable to load OpenAPI plugin from assembly resource '{resourceName}'.");
    }
}
