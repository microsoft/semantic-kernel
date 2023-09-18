// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Resources;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.TestPlugins;

internal static class ResourcePluginsProvider
{
    /// <summary>
    /// Loads OpenApi document from assembly resource.
    /// </summary>
    /// <param name="resourceName">The resource name.</param>
    /// <returns>The OpenApi document resource stream.</returns>
    public static Stream LoadFromResource(string resourceName)
    {
        var type = typeof(ResourcePluginsProvider);

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName);
        if (stream == null)
        {
            throw new MissingManifestResourceException($"Unable to load OpenApi plugin from assembly resource '{resourceName}'.");
        }

        return stream;
    }
}
