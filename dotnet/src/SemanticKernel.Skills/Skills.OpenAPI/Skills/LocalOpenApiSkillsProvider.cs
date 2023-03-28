// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Resources;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Skills;

/// <summary>
/// OpenApi skill provider.
/// </summary>
public static class LocalOpenApiSkillsProvider
{
    /// <summary>
    /// Azure KeyValut skill name.
    /// </summary>
    public const string AzureKeyVault = "AzureKeyVaultSkill";

    /// <summary>
    /// Loads OpenApi document from assembly resource.
    /// </summary>
    /// <param name="skillName">The skill name.</param>
    /// <returns>The OpenApi document resource stream.</returns>
    public static Stream LoadFroResource(string skillName)
    {
        Verify.ValidSkillName(skillName);

        var type = typeof(LocalOpenApiSkillsProvider);

        var resourceName = $"{skillName}.openapi.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName); //TODO: support yaml resources
        if (stream == null)
        {
            throw new MissingManifestResourceException($"Unable to load OpenApi skill from assembly resource '{resourceName}'.");
        }

        return stream;
    }
}
