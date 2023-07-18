// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql;

using System.Collections.Generic;

/// <summary>
/// Defines the schemas initialized by the console.
/// </summary>
internal static class SchemasDefinitions
{
    /// <summary>
    /// Enumerates the names of the schemas to be registered with the console.
    /// </summary>
    /// <remarks>
    /// After testing with the sample data-sources, try one of your own!
    /// </remarks>
    public static IEnumerable<string> GetNames()
    {
        yield return "adventureworkslt";
        yield return "descriptiontest";
        // TODO: List your own schema here (comment-out others for focused exploration)
    }
}
