// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

/// <summary>
/// HTTP schema to perform oobabooga completion request. Contains many parameters, some of which are specific to certain kinds of models.
/// See <see href="https://github.com/oobabooga/text-generation-webui/blob/main/docs/Generation-parameters.md"/> and subsequent links for additional information.
/// </summary>
[Serializable]
public sealed class TextCompletionRequest
{
    /// <summary>
    /// The prompt text to complete.
    /// </summary>
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; } = string.Empty;

    /// <summary>
    /// The maximum number of tokens to generate, ignoring the number of tokens in the prompt.
    /// </summary>
    [JsonPropertyName("max_new_tokens")]
    public int? MaxNewTokens { get; set; }

    /// <summary>
    /// Determines whether or not to use sampling; use greedy decoding if false.
    /// </summary>
    [JsonPropertyName("do_sample")]
    public bool DoSample { get; set; } = true;

    /// <summary>
    /// Modulates the next token probabilities. A value of 0 implies deterministic output (only the most likely token is used). Higher values increase randomness.
    /// </summary>
    [JsonPropertyName("temperature")]
    public double Temperature { get; set; }

    /// <summary>
    /// If set to a value less than 1, only the most probable tokens with cumulative probability less than this value are kept for generation.
    /// </summary>
    [JsonPropertyName("top_p")]
    public double TopP { get; set; }

    /// <summary>
    /// Measures how similar the conditional probability of predicting a target token is to the expected conditional probability of predicting a random token, given the generated text.
    /// </summary>
    [JsonPropertyName("typical_p")]
    public double TypicalP { get; set; } = 1;

    /// <summary>
    /// Sets a probability floor below which tokens are excluded from being sampled.
    /// </summary>
    [JsonPropertyName("epsilon_cutoff")]
    public double EpsilonCutoff { get; set; }

    /// <summary>
    /// Used with top_p, top_k, and epsilon_cutoff set to 0. This parameter hybridizes locally typical sampling and epsilon sampling.
    /// </summary>
    [JsonPropertyName("eta_cutoff")]
    public double EtaCutoff { get; set; }

    /// <summary>
    /// Controls Tail Free Sampling (value between 0 and 1)
    /// </summary>
    [JsonPropertyName("tfs")]
    public double Tfs { get; set; } = 1;

    /// <summary>
    /// Top A Sampling is a way to pick the next word in a sentence based on how important it is in the context. Top-A considers the probability of the most likely token, and sets a limit based on its percentage. After this, remaining tokens are compared to this limit. If their probability is too low, they are removed from the pool​.
    /// </summary>
    [JsonPropertyName("top_a")]
    public double TopA { get; set; }

    /// <summary>
    /// Exponential penalty factor for repeating prior tokens. 1 means no penalty, higher value = less repetition.
    /// </summary>
    [JsonPropertyName("repetition_penalty")]
    public double RepetitionPenalty { get; set; } = 1.18;

    /// <summary>
    ///When using "top k", you select the top k most likely words to come next based on their probability of occurring, where k is a fixed number that you specify. You can use Top_K to control the amount of diversity in the model output​
    /// </summary>
    [JsonPropertyName("top_k")]
    public int TopK { get; set; }

    /// <summary>
    /// Minimum length of the sequence to be generated.
    /// </summary>
    [JsonPropertyName("min_length")]
    public int MinLength { get; set; }

    /// <summary>
    /// If set to a value greater than 0, all ngrams of that size can only occur once.
    /// </summary>
    [JsonPropertyName("no_repeat_ngram_size")]
    public int NoRepeatNgramSize { get; set; }

    /// <summary>
    /// Number of beams for beam search. 1 means no beam search.
    /// </summary>
    [JsonPropertyName("num_beams")]
    public int NumBeams { get; set; } = 1;

    /// <summary>
    /// The values balance the model confidence and the degeneration penalty in contrastive search decoding.
    /// </summary>
    [JsonPropertyName("penalty_alpha")]
    public int PenaltyAlpha { get; set; }

    /// <summary>
    /// Exponential penalty to the length that is used with beam-based generation
    /// </summary>
    [JsonPropertyName("length_penalty")]
    public double LengthPenalty { get; set; } = 1;

    /// <summary>
    ///  Controls the stopping condition for beam-based methods, like beam-search. It accepts the following values: True, where the generation stops as soon as there are num_beams complete candidates; False, where an heuristic is applied and the generation stops when is it very unlikely to find better candidates.
    /// </summary>
    [JsonPropertyName("early_stopping")]
    public bool EarlyStopping { get; set; }

    /// <summary>
    /// Parameter used for mirostat sampling in Llama.cpp, controlling perplexity during text (default: 0, 0 = disabled, 1 = Mirostat, 2 = Mirostat 2.0)
    /// </summary>
    [JsonPropertyName("mirostat_mode")]
    public int MirostatMode { get; set; }

    /// <summary>
    /// Set the Mirostat target entropy, parameter tau (default: 5.0)
    /// </summary>
    [JsonPropertyName("mirostat_tau")]
    public int MirostatTau { get; set; } = 5;

    /// <summary>
    /// Set the Mirostat learning rate, parameter eta (default: 0.1)
    /// </summary>
    [JsonPropertyName("mirostat_eta")]
    public double MirostatEta { get; set; } = 0.1;

    /// <summary>
    /// Random seed to control sampling, used when DoSample is True.
    /// </summary>
    [JsonPropertyName("seed")]
    public int Seed { get; set; } = -1;

    /// <summary>
    /// Controls whether to add beginning of a sentence token
    /// </summary>
    [JsonPropertyName("add_bos_token")]
    public bool AddBosToken { get; set; } = true;

    /// <summary>
    /// The leftmost tokens are removed if the prompt exceeds this length. Most models require this to be at most 2048.
    /// </summary>
    [JsonPropertyName("truncation_length")]
    public int TruncationLength { get; set; } = 2048;

    /// <summary>
    /// Forces the model to never end the generation prematurely.
    /// </summary>
    [JsonPropertyName("ban_eos_token")]
    public bool BanEosToken { get; set; } = true;

    /// <summary>
    /// Some specific models need this unset.
    /// </summary>
    [JsonPropertyName("skip_special_tokens")]
    public bool SkipSpecialTokens { get; set; } = true;

    /// <summary>
    /// In addition to the defaults. Written between "" and separated by commas. For instance: "\nYour Assistant:", "\nThe assistant:"
    /// </summary>
    [JsonPropertyName("stopping_strings")]
    public List<string> StoppingStrings { get; set; } = new List<string>();
}
