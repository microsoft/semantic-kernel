// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Resources;

namespace SemanticKernel.Skills.UnitTests.Grpc.Protobuf.TestSkills;

internal static class ResourceSkillsProvider
{
    /// <summary>
    /// Loads .proto file from assembly resource.
    /// </summary>
    /// <param name="resourceName">The resource name.</param>
    /// <returns>The OpenApi document resource stream.</returns>
    public static Stream LoadFromResource(string resourceName)
    {
        var type = typeof(ResourceSkillsProvider);

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName);
        if (stream == null)
        {
            throw new MissingManifestResourceException($"Unable to load gRPC skill from assembly resource '{resourceName}'.");
        }

        return stream;
    }
}
