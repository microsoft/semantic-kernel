// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Prompty.Core;

/// <summary>Parameters to be sent to the model.</summary>
internal sealed class PromptyModelParameters
{
    /// <summary>Specify the format for model output (e.g., JSON mode).</summary>
    [YamlMember(Alias = "response_format")]
    public PromptyResponseFormat? ResponseFormat { get; set; }

    /// <summary>Seed for deterministic sampling (Beta feature).</summary>
    [YamlMember(Alias = "seed")]
    public int? Seed { get; set; }

    /// <summary>Maximum number of tokens in chat completion.</summary>
    [YamlMember(Alias = "max_tokens")]
    public int? MaxTokens { get; set; }

    /// <summary>Sampling temperature (0 means deterministic).</summary>
    [YamlMember(Alias = "temperature")]
    public double? Temperature { get; set; }

    /// <summary>Controls which function the model calls (e.g., "none" or "auto").</summary>
    [YamlMember(Alias = "tools_choice")]
    public string? ToolsChoice { get; set; }

    /// <summary>Array of tools (if applicable).</summary>
    [YamlMember(Alias = "tools")]
    public List<PromptyTool>? Tools { get; set; }

    /// <summary>Frequency penalty for sampling.</summary>
    [YamlMember(Alias = "frequency_penalty")]
    public double? FrequencyPenalty { get; set; }

    /// <summary>Presence penalty for sampling.</summary>
    [YamlMember(Alias = "presence_penalty")]
    public double? PresencePenalty { get; set; }

    /// <summary>Sequences where model stops generating tokens.</summary>
    [YamlMember(Alias = "stop")]
    public List<string>? Stop { get; set; }

    /// <summary>Nucleus sampling probability (0 means no tokens generated).</summary>
    [YamlMember(Alias = "top_p")]
    public double? TopP { get; set; }
}
