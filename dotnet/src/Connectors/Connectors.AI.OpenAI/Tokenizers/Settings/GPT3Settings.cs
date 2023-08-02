// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers.Settings;

internal static class GPT3Settings
{
    /// <summary>Gets the cached encoding table (encoder.json).</summary>
    internal static Dictionary<string, int> Encoder => s_encoder.Value;

    /// <summary>Gets the cached byte pair encoding table (vocab.bpe).</summary>
    internal static Dictionary<(string, string), int> BpeRanks => s_bpeRanks.Value;

    /// <summary>Lazy load the cached encoding table (encoder.json).</summary>
    private static readonly Lazy<Dictionary<string, int>> s_encoder = new(() =>
        JsonSerializer.Deserialize<Dictionary<string, int>>(
            EmbeddedResource.ReadEncodingTable()) ?? throw new AIException(
            AIException.ErrorCodes.InvalidConfiguration,
            "Encoding table deserialization returned NULL"));

    /// <summary>Lazy load the cached byte pair encoding table (vocab.bpe).</summary>
    private static readonly Lazy<Dictionary<(string, string), int>> s_bpeRanks = new(() =>
    {
        string table = EmbeddedResource.ReadBytePairEncodingTable();
        Debug.Assert(table.StartsWith("#version: 0.2", StringComparison.Ordinal));

        // Skip past the header line
        int pos = table.IndexOf('\n') + 1;
        Debug.Assert(pos > 0);

        // For each line, split on the first space and add the pair to the dictionary as a key with the value being the entry number.
        var result = new Dictionary<(string, string), int>();
        int nextPos;
        while ((nextPos = table.IndexOf('\n', pos)) >= 0)
        {
            ReadOnlySpan<char> span = table.AsSpan(pos, nextPos - pos).Trim();
            pos = span.IndexOf(' ');
            if (pos >= 0)
            {
                result.Add((span.Slice(0, pos).ToString(), span.Slice(pos + 1).ToString()), result.Count);
            }

            pos = nextPos + 1;
        }

        return result;
    });
}
