// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

/// <summary>
/// HTTP schema to perform completion request.
/// </summary>
[Serializable]
public sealed class TextCompletionRequest
{
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; }

    [JsonPropertyName("max_new_tokens")]
    public int MaxNewTokens { get; set; }

    [JsonPropertyName("do_sample")]
    public bool DoSample { get; set; } = true;

    [JsonPropertyName("temperature")]
    public double Temperature { get; set; }

    [JsonPropertyName("top_p")]
    public double TopP { get; set; }

    [JsonPropertyName("typical_p")]
    public double TypicalP { get; set; } = 1;

    [JsonPropertyName("epsilon_cutoff")]
    public int EpsilonCutoff { get; set; }

    [JsonPropertyName("eta_cutoff")]
    public int EtaCutoff { get; set; }

    [JsonPropertyName("tfs")]
    public int Tfs { get; set; } = 1;

    [JsonPropertyName("top_a")]
    public int TopA { get; set; }

    [JsonPropertyName("repetition_penalty")]
    public double RepetitionPenalty { get; set; } = 1.18;

    [JsonPropertyName("top_k")]
    public int TopK { get; set; }

    [JsonPropertyName("min_length")]
    public int MinLength { get; set; }

    [JsonPropertyName("no_repeat_ngram_size")]
    public int NoRepeatNgramSize { get; set; }

    [JsonPropertyName("num_beams")]
    public int NumBeams { get; set; } = 1;

    [JsonPropertyName("penalty_alpha")]
    public int PenaltyAlpha { get; set; }

    [JsonPropertyName("length_penalty")]
    public double LengthPenalty { get; set; } = 1;

    [JsonPropertyName("early_stopping")]
    public bool EarlyStopping { get; set; }

    [JsonPropertyName("mirostat_mode")]
    public int MirostatMode { get; set; }

    [JsonPropertyName("mirostat_tau")]
    public int MirostatTau { get; set; } = 5;

    [JsonPropertyName("mirostat_eta")]
    public double MirostatEta { get; set; } = 0.1;

    [JsonPropertyName("seed")]
    public int Seed { get; set; } = -1;

    [JsonPropertyName("add_bos_token")]
    public bool AddBosToken { get; set; } = true;

    [JsonPropertyName("truncation_length")]
    public int TruncationLength { get; set; } = 2048;

    [JsonPropertyName("ban_eos_token")]
    public bool BanEosToken { get; set; } = true;

    [JsonPropertyName("skip_special_tokens")]
    public bool SkipSpecialTokens { get; set; }

    [JsonPropertyName("stopping_strings")]
    public List<string> StoppingStrings { get; set; }
}
