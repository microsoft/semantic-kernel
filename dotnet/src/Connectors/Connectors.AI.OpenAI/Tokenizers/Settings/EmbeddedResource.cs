// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers.Settings;

internal static class EmbeddedResource
{
    /// <summary>
    /// Return content of BPE file.
    /// </summary>
    /// <returns>BPE file content</returns>
    internal static string ReadBytePairEncodingTable()
    {
        Stream? stream = typeof(EmbeddedResource).Assembly.GetManifestResourceStream("vocab.bpe");
        if (stream is null)
        {
            throw new InvalidOperationException("vocab.bpe not found");
        }

        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }

    /// <summary>
    /// Return content of encoding table file.
    /// </summary>
    /// <returns>Encoding table string</returns>
    internal static string ReadEncodingTable()
    {
        Stream? stream = typeof(EmbeddedResource).Assembly.GetManifestResourceStream("encoder.json");
        if (stream is null)
        {
            throw new InvalidOperationException("encoder.json not found");
        }

        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}
