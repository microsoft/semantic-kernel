// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import reactor.util.annotation.Nullable;

import java.util.ArrayList;
import java.util.List;

/** Prompt template configuration */
public class PromptTemplateConfig {
    private final CompletionConfig completionConfig;
    private final InputConfig input;

    /**
     * A returns the configuration for the text completion
     *
     * @return
     */
    public CompletionConfig getCompletionConfig() {
        return completionConfig;
    }

    /** Completion configuration parameters */
    public static class CompletionConfig {
        /*
        /// <summary>
        /// Sampling temperature to use, between 0 and 2. Higher values will make the output more random.
        /// Lower values will make it more focused and deterministic.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonPropertyOrder(1)]
        */
        private final double temperature;
        /*
        /// <summary>
        /// Cut-off of top_p probability mass of tokens to consider.
        /// For example, 0.1 means only the tokens comprising the top 10% probability mass are considered.
        /// </summary>
        [JsonPropertyName("top_p")]
        [JsonPropertyOrder(2)]
        */
        private final double topP;

        /*
        /// <summary>
        /// Lowers the probability of a word appearing if it already appeared in the predicted text.
        /// Unlike the frequency penalty, the presence penalty does not depend on the frequency at which words
        /// appear in past predictions.
        /// </summary>
        [JsonPropertyName("presence_penalty")]
        [JsonPropertyOrder(3)]
        */
        private final double presencePenalty;

        /*
        /// <summary>
        /// Controls the model’s tendency to repeat predictions. The frequency penalty reduces the probability
        /// of words that have already been generated. The penalty depends on how many times a word has already
        /// occurred in the prediction.
        /// </summary>
        [JsonPropertyName("frequency_penalty")]
        [JsonPropertyOrder(4)]
        */
        private final double frequencyPenalty;
        /*
        /// <summary>
        /// Maximum number of tokens that can be generated.
        /// </summary>
        [JsonPropertyName("max_tokens")]
        [JsonPropertyOrder(5)]*/
        private final int maxTokens; // { get; set; } = 256;
        /*
        /// <summary>
        /// Stop sequences are optional sequences that tells the AI model when to stop generating tokens.
        /// </summary>
        [JsonPropertyName("stop_sequences")]
        [JsonPropertyOrder(6)]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        */
        public final List<String> stopSequences; // { get; set; } = new();

        public CompletionConfig() {
            this(0.0, 0.0, 0.0, 0.0, 256, new ArrayList<>());
        }

        @JsonCreator
        public CompletionConfig(
                @JsonProperty("temperature") double temperature,
                @JsonProperty("top_p") double topP,
                @JsonProperty("presence_penalty") double presencePenalty,
                @JsonProperty("frequency_penalty") double frequencyPenalty,
                @JsonProperty("max_tokens") int maxTokens,
                @JsonProperty(value = "stop_sequences") List<String> stopSequences) {
            this.temperature = temperature;
            this.topP = topP;
            this.presencePenalty = presencePenalty;
            this.frequencyPenalty = frequencyPenalty;
            this.maxTokens = maxTokens;
            if (stopSequences == null) {
                stopSequences = new ArrayList<>();
            }
            this.stopSequences = stopSequences;
        }

        public double getTemperature() {
            return temperature;
        }

        public double getTopP() {
            return topP;
        }

        public double getPresencePenalty() {
            return presencePenalty;
        }

        public double getFrequencyPenalty() {
            return frequencyPenalty;
        }

        public int getMaxTokens() {
            return maxTokens;
        }
    }

    /** Input parameter for semantic functions */
    public static class InputParameter {
        private final String name;
        private final String description;

        private final String defaultValue;

        @JsonCreator
        public InputParameter(
                @JsonProperty("name") String name,
                @JsonProperty("description") String description,
                @JsonProperty("defaultValue") String defaultValue) {
            this.name = name;
            this.description = description;
            this.defaultValue = defaultValue;
        }
    }

    /** Input configuration (list of all input parameters for a semantic function). */
    public static class InputConfig {

        public final List<InputParameter> parameters;

        @JsonCreator
        public InputConfig(@JsonProperty("parameters") List<InputParameter> parameters) {
            this.parameters = parameters;
        }
    }

    /*
    /// <summary>
    /// Schema - Not currently used.
    /// </summary>
    [JsonPropertyName("schema")]
    [JsonPropertyOrder(1)]
    public int Schema { get; set; } = 1;

    /// <summary>
    /// Type, such as "completion", "embeddings", etc.
    /// </summary>
    /// <remarks>TODO: use enum</remarks>
    [JsonPropertyName("type")]
    [JsonPropertyOrder(2)]
    */
    private final int schema;

    private final String type; // { get; set; } = "completion";
    /*
        /// <summary>
        /// Description
        /// </summary>
        [JsonPropertyName("description")]
        [JsonPropertyOrder(3)]
    */
    private final String description;

    public PromptTemplateConfig(
            String description, String type, @Nullable CompletionConfig completionConfig) {
        this(1, description, type, completionConfig, new InputConfig(new ArrayList<>()));
    }

    @JsonCreator
    public PromptTemplateConfig(
            @JsonProperty("schema") int schema,
            @JsonProperty("description") String description,
            @JsonProperty("type") String type,
            @Nullable @JsonProperty("completion") CompletionConfig completionConfig,
            @JsonProperty("input") InputConfig input) {
        if (completionConfig == null) {
            completionConfig = new CompletionConfig();
        }
        this.schema = schema;
        this.description = description;
        this.type = type;
        this.completionConfig = completionConfig;
        this.input = input;
    }

    public String getDescription() {
        return description;
    }

    /*
    /// <summary>
    /// Completion configuration parameters.
    /// </summary>
    [JsonPropertyName("completion")]
    [JsonPropertyOrder(4)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]

     */
    // private final CompletionConfig completion = null;

    /*

        /// <summary>
        /// Default AI services to use.
        /// </summary>
        [JsonPropertyName("default_services")]
        [JsonPropertyOrder(5)]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public List<string> DefaultServices { get; set; } = new();

        /// <summary>
        /// Input configuration (that is, list of all input parameters).
        /// </summary>
        [JsonPropertyName("input")]
        [JsonPropertyOrder(6)]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public InputConfig Input { get; set; } = new();

        /// <summary>
        /// Remove some default properties to reduce the JSON complexity.
        /// </summary>
        /// <returns>Compacted prompt template configuration.</returns>
        public PromptTemplateConfig Compact()
        {
            if (this.Completion.StopSequences.Count == 0)
            {
                this.Completion.StopSequences = null!;
            }

            if (this.DefaultServices.Count == 0)
            {
                this.DefaultServices = null!;
            }

            return this;
        }

    /// <summary>
    /// Creates a prompt template configuration from JSON.
    /// </summary>
    /// <param name="json">JSON of the prompt template configuration.</param>
    /// <returns>Prompt template configuration.</returns>
    public static PromptTemplateConfig FromJson(String json) throws JsonProcessingException {
        return new ObjectMapper().readValue(json, PromptTemplateConfig.class);
    }
         */

}
