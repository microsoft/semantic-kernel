// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Newtonsoft.Json;

#pragma warning disable CS8618

namespace AIPlugins.AzureFunctions.Generator.Models;

internal class PromptConfig
{
    [JsonProperty("schema")]
    public int Schema { get; set; }

    [JsonProperty("type")]
    public string Type { get; set; }

    [JsonProperty("description")]
    public string Description { get; set; }

    [JsonProperty("completion")]
    public CompletionConfig Completion { get; set; }

    [JsonProperty("input")]
    public InputConfig? Input { get; set; }

    public class CompletionConfig
    {
        [JsonProperty("max_tokens")]
        public int MaxTokens { get; set; }

        [JsonProperty("temperature")]
        public double Temperature { get; set; }

        [JsonProperty("top_p")]
        public double TopP { get; set; }

        [JsonProperty("presence_penalty")]
        public double PresencePenalty { get; set; }

        [JsonProperty("frequency_penalty")]
        public double FrequencyPenalty { get; set; }
    }

    public class InputConfig
    {
        [JsonProperty("parameters")]
        public List<ParameterConfig> Parameters { get; set; }
    }

    public class ParameterConfig
    {
        [JsonProperty("name")]
        public string Name { get; set; }

        [JsonProperty("description")]
        public string Description { get; set; }

        [JsonProperty("defaultValue")]
        public string DefaultValue { get; set; }
    }
}
