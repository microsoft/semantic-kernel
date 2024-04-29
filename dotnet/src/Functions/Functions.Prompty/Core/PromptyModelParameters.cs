// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Prompty.Core;

internal sealed class PromptyModelParameters
{
    // Parameters to be sent to the model
    [YamlMember(Alias = "response_format")]
    public string? ResponseFormat { get; set; } // Specify the format for model output (e.g., JSON mode)

    [YamlMember(Alias = "seed")]
    public int? Seed { get; set; } // Seed for deterministic sampling (Beta feature)

    [YamlMember(Alias = "max_tokens")]
    public int? MaxTokens { get; set; } // Maximum number of tokens in chat completion

    [YamlMember(Alias = "temperature")]
    public double? Temperature { get; set; } // Sampling temperature (0 means deterministic)

    [YamlMember(Alias = "tools_choice")]
    public string? ToolsChoice { get; set; } // Controls which function the model calls (e.g., "none" or "auto")

    [YamlMember(Alias = "tools")]
    public List<PromptyTool>? Tools { get; set; } // Array of tools (if applicable)

    [YamlMember(Alias = "frequency_penalty")]
    public double? FrequencyPenalty { get; set; } // Frequency penalty for sampling

    [YamlMember(Alias = "presence_penalty")]
    public double? PresencePenalty { get; set; } // Presence penalty for sampling

    [YamlMember(Alias = "stop")]
    public List<string>? Stop { get; set; } // Sequences where model stops generating tokens

    [YamlMember(Alias = "top_p")]
    public double? TopP { get; set; } // Nucleus sampling probability (0 means no tokens generated)
}
