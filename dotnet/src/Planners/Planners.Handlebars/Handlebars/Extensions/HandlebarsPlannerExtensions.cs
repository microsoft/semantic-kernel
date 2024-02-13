// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Extension methods for the <see cref="HandlebarsPlanner"/> interface.
/// </summary>
internal static class HandlebarsPlannerExtensions
{
    /// <summary>
    /// Reads the prompt for the given file name.
    /// </summary>
    /// <param name="planner">The handlebars planner.</param>
    /// <param name="fileName">The name of the file to read.</param>
    /// <param name="additionalNameSpace">The name of the additional namespace.</param>
    /// <returns>The content of the file as a string.</returns>
    public static string ReadPrompt(this HandlebarsPlanner planner, string fileName, string? additionalNameSpace = "")
    {
        using var stream = planner.ReadPromptStream(fileName, additionalNameSpace);
        using var reader = new StreamReader(stream);

        return reader.ReadToEnd();
    }

    /// <summary>
    /// Reads the prompt stream for the given file name.
    /// </summary>
    /// <param name="planner">The handlebars planner.</param>
    /// <param name="fileName">The name of the file to read.</param>
    /// <param name="additionalNamespace">The name of the additional namespace.</param>
    /// <returns>The stream for the given file name.</returns>
    public static Stream ReadPromptStream(this HandlebarsPlanner planner, string fileName, string? additionalNamespace = "")
    {
        var assembly = Assembly.GetExecutingAssembly();
        var plannerNamespace = planner.GetType().Namespace;
        var targetNamespace = !string.IsNullOrEmpty(additionalNamespace) ? $".{additionalNamespace}" : string.Empty;
        var resourceName = $"{plannerNamespace}{targetNamespace}.{fileName}";

        return assembly.GetManifestResourceStream(resourceName)!;
    }

    /// <summary>
    /// Constructs a Handblebars prompt from the given file name and corresponding partials, if any.
    /// Partials must be contained in a directory following the naming convention: "{promptName}Partials" and loaded inline first to avoid reference errors.
    /// </summary>
    /// <param name="planner">The handlebars planner.</param>
    /// <param name="promptName">The name of the file to read.</param>
    /// <param name="additionalNamespace">The name of the additional namespace.</param>
    /// <returns>The constructed prompt.</returns>
    public static string ConstructHandlebarsPrompt(this HandlebarsPlanner planner, string promptName, string? additionalNamespace = "")
    {
        var partials = planner.ReadAllPromptPartials(promptName, additionalNamespace);
        var prompt = planner.ReadPrompt($"{promptName}.handlebars", additionalNamespace);
        return partials + prompt;
    }

    /// <summary>
    /// Reads all embedded Handlebars prompt partials from the Handlebars Planner `PromptPartials` namespace and concatenates their contents.
    /// </summary>
    /// <param name="planner">The handlebars planner.</param>
    /// <param name="promptName">The name of the parent Handlebars prompt file.</param>
    /// <param name="additionalNamespace">The name of the additional namespace.</param>
    /// <returns>The concatenated content of the embedded partials within the Handlebars Planner namespace.</returns>
    public static string ReadAllPromptPartials(this HandlebarsPlanner planner, string promptName, string? additionalNamespace = "")
    {
        var assembly = Assembly.GetExecutingAssembly();
        var plannerNamespace = planner.GetType().Namespace;
        var parentNamespace = !string.IsNullOrEmpty(additionalNamespace) ? $"{plannerNamespace}.{additionalNamespace}" : plannerNamespace;
        var targetNamespace = $"{parentNamespace}.{promptName}Partials";

        var resourceNames = assembly.GetManifestResourceNames()
            .Where(name =>
                name.StartsWith(targetNamespace, StringComparison.CurrentCulture)
                && name.EndsWith(".handlebars", StringComparison.CurrentCulture))
            // Sort by the number of dots in the name (subdirectory depth), loading subdirectories first, as the outer partials have dependencies on the inner ones.
            .OrderByDescending(name => name.Count(c => c == '.'))
            // then by the name itself
            .ThenBy(name => name);

        var stringBuilder = new StringBuilder();
        foreach (var resourceName in resourceNames)
        {
            using Stream resourceStream = assembly.GetManifestResourceStream(resourceName);
            if (resourceStream != null)
            {
                using var reader = new StreamReader(resourceStream);
                stringBuilder.AppendLine(reader.ReadToEnd());
            }
        }

        return stringBuilder.ToString();
    }
}
