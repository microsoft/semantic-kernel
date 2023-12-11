// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;

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
        var name = planner.GetType().Namespace;
        var supplementalNamespace = !string.IsNullOrEmpty(additionalNamespace) ? $".{additionalNamespace}" : string.Empty;
        var resourceName = $"{name}{supplementalNamespace}.{fileName}";

        return assembly.GetManifestResourceStream(resourceName)!;
    }
}
