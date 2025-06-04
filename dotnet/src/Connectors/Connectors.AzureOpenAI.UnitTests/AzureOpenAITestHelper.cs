// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Net.Http;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests;

/// <summary>
/// Helper for AzureOpenAI test purposes.
/// </summary>
internal static class AzureOpenAITestHelper
{
    /// <summary>
    /// Reads test response from file for mocking purposes.
    /// </summary>
    /// <param name="fileName">Name of the file with test response.</param>
    internal static string GetTestResponse(string fileName)
    {
        return File.ReadAllText($"./TestData/{fileName}");
    }

    /// <summary>
    /// Reads test response from file and create <see cref="StreamContent"/>.
    /// </summary>
    /// <param name="fileName">Name of the file with test response.</param>
    internal static StreamContent GetTestResponseAsStream(string fileName)
    {
        return new StreamContent(File.OpenRead($"./TestData/{fileName}"));
    }
}
