// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;

namespace Microsoft.SemanticKernel.Connectors.OpenAI.Tokenizers.Settings;

internal static class EmbeddedResource
{
    private const string PrefixToIgnore = "Microsoft.SemanticKernel";
    private static readonly string s_namespace = typeof(EmbeddedResource).Namespace;

    /// <summary>
    /// Return content of BPE file.
    /// </summary>
    /// <returns>BPE file content</returns>
    internal static string ReadBytePairEncodingTable()
    {
        return ReadFile("vocab.bpe");
    }

    /// <summary>
    /// Return content of encoding table file.
    /// </summary>
    /// <returns>Encoding table string</returns>
    internal static string ReadEncodingTable()
    {
        return ReadFile("encoder.json");
    }

    /// <summary>
    /// Read a content file embedded in the project. Files are read from disk,
    /// not from the assembly, to avoid inflating the assembly size.
    /// </summary>
    /// <param name="fileName">Filename to read</param>
    /// <returns>File content</returns>
    /// <exception cref="FileNotFoundException">Error in case the file doesn't exist</exception>
    private static string ReadFile(string fileName)
    {
        // Assume the class namespace matches the directory structure to find the file
        var dir = s_namespace
            .Replace(PrefixToIgnore, "", StringComparison.OrdinalIgnoreCase)
            .Trim('.')
            .Replace('.', Path.DirectorySeparatorChar);

        var file = Path.Join(dir, fileName);

        if (!File.Exists(file)) { throw new FileNotFoundException(file); }

        return File.ReadAllText(file);
    }
}
