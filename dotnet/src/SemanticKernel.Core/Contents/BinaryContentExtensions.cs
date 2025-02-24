// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for interacting with <see cref="BinaryContent"/>.
/// </summary>
public static class BinaryContentExtensions
{
    /// <summary>
    /// Writes the content to a file.
    /// </summary>
    /// <param name="content">The content to write.</param>
    /// <param name="filePath">The path to the file to write to.</param>
    /// <param name="overwrite">Whether to overwrite the file if it already exists.</param>
    public static void WriteToFile(this BinaryContent content, string filePath, bool overwrite = false)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("File path cannot be null or empty", nameof(filePath));
        }

        if (!overwrite && File.Exists(filePath))
        {
            throw new InvalidOperationException("File already exists.");
        }

        if (!content.CanRead)
        {
            throw new InvalidOperationException("No content to write to file.");
        }

        File.WriteAllBytes(filePath, content.Data!.Value.ToArray());
    }
}
