// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.Tokenizers.Settings;

internal static class GPT3Settings
{
    // Lazy load and cache encoding table (encoder.json)
    internal static Dictionary<string, int> Encoder => s_encoder.Value;

    // Lazy load and cache byte pair encoding table (vocab.bpe)
    internal static Dictionary<Tuple<string, string>, int> BpeRanks => s_bpeRanks.Value;

    // Lazy load and cache encoding table (encoder.json)
    private static readonly Lazy<Dictionary<string, int>> s_encoder = new(BuildEncoder);

    // Lazy load and cache byte pair encoding table (vocab.bpe)
    private static readonly Lazy<Dictionary<Tuple<string, string>, int>> s_bpeRanks = new(BuildBpeRanks);

    private static Dictionary<Tuple<string, string>, int> BuildBpeRanks()
    {
        string[] lines = EmbeddedResource.ReadBytePairEncodingTable().Split('\n');
        List<Tuple<string, string>> bpeMerges = new ArraySegment<string>(lines, 1, lines.Length - 1)
            .Where(x => x.Trim().Length > 0)
            .Select(x =>
            {
                string[] y = x.Split(' ');
                return new Tuple<string, string>(y[0], y[1]);
            }).ToList();
        return DictZip(bpeMerges, Range(0, bpeMerges.Count));
    }

    private static Dictionary<string, int> BuildEncoder()
    {
        string json = EmbeddedResource.ReadEncodingTable();
        var encoder = JsonSerializer.Deserialize<Dictionary<string, int>>(json);

        return encoder
               ?? throw new AIException(AIException.ErrorCodes.InvalidConfiguration,
                   "Encoding table deserialization returned NULL");
    }

    private static Dictionary<Tuple<string, string>, int> DictZip(List<Tuple<string, string>> x, List<int> y)
    {
        var result = new Dictionary<Tuple<string, string>, int>();
        for (int i = 0; i < x.Count; i++)
        {
            result.Add(x[i], y[i]);
        }

        return result;
    }

    private static List<int> Range(int x, int y)
    {
        return Enumerable.Range(x, y - x).ToList();
    }
}
