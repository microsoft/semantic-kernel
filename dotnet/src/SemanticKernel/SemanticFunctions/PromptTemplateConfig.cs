// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.SemanticFunctions;

public class PromptTemplateConfig
{
    public class CompletionConfig
    {
        [JsonPropertyName("temperature")]
        [JsonPropertyOrder(1)]
        public double Temperature { get; set; } = 0.0f;

        [JsonPropertyName("top_p")]
        [JsonPropertyOrder(2)]
        public double TopP { get; set; } = 0.0f;

        [JsonPropertyName("presence_penalty")]
        [JsonPropertyOrder(3)]
        public double PresencePenalty { get; set; } = 0.0f;

        [JsonPropertyName("frequency_penalty")]
        [JsonPropertyOrder(4)]
        public double FrequencyPenalty { get; set; } = 0.0f;

        [JsonPropertyName("max_tokens")]
        [JsonPropertyOrder(5)]
        public int MaxTokens { get; set; } = 256;

        [JsonPropertyName("stop_sequences")]
        [JsonPropertyOrder(6)]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public List<string> StopSequences { get; set; } = new();
    }

    public class InputParameter
    {
        /// <summary>
        /// Name of the parameter to pass to the function.
        /// e.g. when using "{{$input}}" the name is "input", when using "{{$style}}" the name is "style", etc.
        /// </summary>
        [JsonPropertyName("name")]
        [JsonPropertyOrder(1)]
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Parameter description for UI apps and planner. Localization is not supported here.
        /// </summary>
        [JsonPropertyName("description")]
        [JsonPropertyOrder(2)]
        public string Description { get; set; } = string.Empty;

        /// <summary>
        /// DEfault value when nothing is provided.
        /// </summary>
        [JsonPropertyName("defaultValue")]
        [JsonPropertyOrder(3)]
        public string DefaultValue { get; set; } = string.Empty;
    }

    public class InputConfig
    {
        [JsonPropertyName("parameters")]
        [JsonPropertyOrder(1)]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public List<InputParameter> Parameters { get; set; } = new();
    }

    [JsonPropertyName("schema")]
    [JsonPropertyOrder(1)]
    public int Schema { get; set; } = 1;

    // TODO: use enum
    [JsonPropertyName("type")]
    [JsonPropertyOrder(2)]
    public string Type { get; set; } = "completion";

    [JsonPropertyName("description")]
    [JsonPropertyOrder(3)]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("completion")]
    [JsonPropertyOrder(4)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public CompletionConfig Completion { get; set; } = new();

    [JsonPropertyName("default_backends")]
    [JsonPropertyOrder(5)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string> DefaultBackends { get; set; } = new();

    [JsonPropertyName("input")]
    [JsonPropertyOrder(6)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public InputConfig Input { get; set; } = new();

    // Remove some default properties to reduce the JSON complexity
    public PromptTemplateConfig Compact()
    {
        if (this.Completion.StopSequences.Count == 0)
        {
            this.Completion.StopSequences = null!;
        }

        if (this.DefaultBackends.Count == 0)
        {
            this.DefaultBackends = null!;
        }

        return this;
    }

    public static PromptTemplateConfig FromJson(string json)
    {
        var result = Json.Deserialize<PromptTemplateConfig>(json);
        Verify.NotNull(result, "Unable to deserialize prompt template config. The deserialized returned NULL.");
        return result;
    }
}
