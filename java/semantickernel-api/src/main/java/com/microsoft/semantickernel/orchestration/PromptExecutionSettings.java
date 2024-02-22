// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;

/**
 * Configuration settings for prompt execution.
 */
public class PromptExecutionSettings {

    public static final String DEFAULT_SERVICE_ID = "default";
    public static final Integer DEFAULT_MAX_TOKENS = 256;
    public static final Double DEFAULT_TEMPERATURE = 1.0;
    public static final Double DEFAULT_TOP_P = 1.0;
    public static final Double DEFAULT_PRESENCE_PENALTY = 0.0;
    public static final Double DEFAULT_FREQUENCY_PENALTY = 0.0;
    public static final Integer DEFAULT_BEST_OF = 1;
    public static final Integer DEFAULT_RESULTS_PER_PROMPT = 1;

    private static final String SERVICE_ID = "service_id";
    private static final String MODEL_ID = "model_id";
    private static final String TEMPERATURE = "temperature";
    private static final String TOP_P = "top_p";
    private static final String PRESENCE_PENALTY = "presence_penalty";
    private static final String FREQUENCY_PENALTY = "frequency_penalty";
    private static final String MAX_TOKENS = "max_tokens";
    private static final String BEST_OF = "best_of";
    private static final String USER = "user";
    private static final String STOP_SEQUENCES = "stop_sequences";
    private static final String RESULTS_PER_PROMPT = "results_per_prompt";
    private static final String TOKEN_SELECTION_BIASES = "token_selection_biases";

    private final String serviceId;
    private final String modelId;
    private final double temperature;
    private final double topP;
    private final double presencePenalty;
    private final double frequencyPenalty;
    private final int maxTokens;
    private final int bestOf;
    private final int resultsPerPrompt;
    private final String user;
    @Nullable
    private final List<String> stopSequences;
    private final Map<Integer, Integer> tokenSelectionBiases;

    /**
     * Create a new instance of PromptExecutionSettings.
     *
     * @param serviceId            The id of the AI service to use for prompt execution.
     * @param modelId              The id of the model to use for prompt execution.
     * @param temperature          The temperature setting for prompt execution.
     * @param topP                 The topP setting for prompt execution.
     * @param presencePenalty      The presence penalty setting for prompt execution.
     * @param frequencyPenalty     The frequency penalty setting for prompt execution.
     * @param maxTokens            The maximum number of tokens to generate in the output.
     * @param resultsPerPrompt     The number of results to generate for each prompt.
     * @param bestOf               The best of setting for prompt execution.
     * @param user                 The user to associate with the prompt execution.
     * @param stopSequences        The stop sequences to use for prompt execution.
     * @param tokenSelectionBiases The token selection biases to use for prompt execution.
     */
    @JsonCreator
    public PromptExecutionSettings(
        @JsonProperty(SERVICE_ID) String serviceId,
        @JsonProperty(MODEL_ID) String modelId,
        @JsonProperty(TEMPERATURE) Double temperature,
        @JsonProperty(TOP_P) Double topP,
        @JsonProperty(PRESENCE_PENALTY) Double presencePenalty,
        @JsonProperty(FREQUENCY_PENALTY) Double frequencyPenalty,
        @JsonProperty(MAX_TOKENS) Integer maxTokens,
        @JsonProperty(RESULTS_PER_PROMPT) Integer resultsPerPrompt,
        @JsonProperty(BEST_OF) Integer bestOf,
        @JsonProperty(USER) String user,
        @Nullable @JsonProperty(STOP_SEQUENCES) List<String> stopSequences,
        @Nullable @JsonProperty(TOKEN_SELECTION_BIASES) Map<Integer, Integer> tokenSelectionBiases) {
        this.serviceId = serviceId;
        this.modelId = modelId;
        this.temperature = clamp(temperature, 0d, 2d, DEFAULT_TEMPERATURE);
        this.topP = clamp(topP, 0d, 1d, DEFAULT_TOP_P);
        this.presencePenalty = clamp(presencePenalty, -2d, 2d, DEFAULT_PRESENCE_PENALTY);
        this.frequencyPenalty = clamp(frequencyPenalty, -2d, 2d, DEFAULT_FREQUENCY_PENALTY);
        this.maxTokens = clamp(maxTokens, 1, Integer.MAX_VALUE, DEFAULT_MAX_TOKENS);
        this.resultsPerPrompt = clamp(resultsPerPrompt, 1, Integer.MAX_VALUE,
            DEFAULT_RESULTS_PER_PROMPT);
        this.bestOf = clamp(bestOf, 1, Integer.MAX_VALUE, DEFAULT_BEST_OF);
        this.user = user;
        this.stopSequences = stopSequences != null ? new ArrayList<>(stopSequences)
            : Collections.emptyList();
        this.tokenSelectionBiases = tokenSelectionBiases != null
            ? new HashMap<>(tokenSelectionBiases)
            : Collections.emptyMap();
        this.tokenSelectionBiases.replaceAll((k, v) -> clamp(v, -100, 100, 0));
    }

    /**
     * Create a new builder for PromptExecutionSettings.
     *
     * @return A new builder for PromptExecutionSettings.
     */
    public static Builder builder() {
        return new Builder();
    }

    private static <T extends Number> T clamp(T value, T min, T max, T defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        if (value.doubleValue() < min.doubleValue()) {
            return min;
        }
        if (value.doubleValue() > max.doubleValue()) {
            return max;
        }
        return value;
    }

    /**
     * Get the id of the AI service to use for prompt execution.
     *
     * @return The id of the AI service to use for prompt execution.
     */
    @JsonProperty(SERVICE_ID)
    public String getServiceId() {
        return serviceId;
    }

    /**
     * Get the id of the model to use for prompt execution.
     *
     * @return The id of the model to use for prompt execution.
     */
    @JsonProperty(MODEL_ID)
    public String getModelId() {
        return modelId;
    }

    /**
     * The temperature setting controls the randomness of the output. Lower values produce more
     * deterministic outputs, while higher values produce more random outputs.
     *
     * @return The temperature setting.
     */
    @JsonProperty(TEMPERATURE)
    public double getTemperature() {
        return Double.isNaN(temperature) ? DEFAULT_TEMPERATURE : temperature;
    }

    /**
     * The topP setting controls how many different words or phrases are considered to predict the
     * next token. The value is a probability threshold, and the model considers the most likely
     * tokens whose cumulative probability mass is greater than the threshold. For example, if the
     * value is 0.1, the model considers only the tokens that make up the top 10% of the cumulative
     * probability mass.
     *
     * @return The topP setting.
     */
    @JsonProperty(TOP_P)
    public double getTopP() {
        return topP;
    }

    /**
     * Presence penalty encourages the model to use a more or less diverse range of tokens in the
     * output. A higher value means that the model will try to use a greater variety of tokens in
     * the ouput.
     *
     * @return The presence penalty setting.
     */
    @JsonProperty(PRESENCE_PENALTY)
    public double getPresencePenalty() {
        return presencePenalty;
    }

    /**
     * Frequency penalty encourages the model to avoid repeating the same token in the output. A
     * higher value means that the model will be less likely to repeat a token.
     *
     * @return The frequency penalty setting.
     */
    @JsonProperty(FREQUENCY_PENALTY)
    public double getFrequencyPenalty() {
        return frequencyPenalty;
    }

    /**
     * The maximum number of tokens to generate in the output.
     *
     * @return The maximum number of tokens to generate in the output.
     */
    @JsonProperty(MAX_TOKENS)
    public int getMaxTokens() {
        return maxTokens;
    }

    /**
     * The number of results to generate for each prompt.
     *
     * @return The number of results to generate for each prompt.
     */
    @JsonProperty(RESULTS_PER_PROMPT)
    public int getResultsPerPrompt() {
        return resultsPerPrompt;
    }

    /**
     * The log probability threshold for a result to be considered.
     *
     * @return The log probability threshold for a result to be considered.
     */
    @JsonProperty(BEST_OF)
    public int getBestOf() {
        // TODO: not present in com.azure:azure-ai-openai
        return bestOf;
    }

    /**
     * The user to associate with the prompt execution.
     *
     * @return The user to associate with the prompt execution.
     */
    @JsonProperty(USER)
    public String getUser() {
        return user;
    }

    /**
     * The stop sequences to use for prompt execution.
     *
     * @return The stop sequences to use for prompt execution.
     */
    @JsonProperty(STOP_SEQUENCES)
    @Nullable
    public List<String> getStopSequences() {
        if (stopSequences != null) {
            return Collections.unmodifiableList(stopSequences);
        }
        return null;
    }

    /**
     * The token selection biases to use for prompt execution. The key is the token id from the
     * tokenizer, and the value is the bias. A negative bias will make the model less likely to use
     * the token, and a positive bias will make the model more likely to use the token.
     *
     * @return The token selection biases to use for prompt execution.
     */
    @JsonProperty(TOKEN_SELECTION_BIASES)
    @Nullable
    public Map<Integer, Integer> getTokenSelectionBiases() {
        if (tokenSelectionBiases != null) {
            return Collections.unmodifiableMap(tokenSelectionBiases);
        }
        return null;
    }

    /**
     * Builder for PromptExecutionSettings.
     */
    public static class Builder {

        Map<String, Object> settings = new HashMap<>();

        /**
         * Set the id of the AI service to use for prompt execution.
         *
         * @param serviceId The id of the AI service to use for prompt execution.
         * @return This builder.
         */
        public Builder withServiceId(String serviceId) {
            settings.put(SERVICE_ID, serviceId);
            return this;
        }

        /**
         * Set the id of the model to use for prompt execution.
         *
         * @param modelId The id of the model to use for prompt execution.
         * @return This builder.
         */
        public Builder withModelId(String modelId) {
            settings.put(MODEL_ID, modelId);
            return this;
        }

        /**
         * Set the temperature setting for prompt execution. The value is clamped to the range [0.0,
         * 2.0], and the default is 1.0.
         *
         * @param temperature The temperature setting for prompt execution.
         * @return This builder.
         */
        public Builder withTemperature(double temperature) {
            if (!Double.isNaN(temperature)) {
                settings.put(TEMPERATURE, temperature);
            }
            return this;
        }

        /**
         * Set the topP setting for prompt execution. The value is clamped to the range [0.0, 1.0],
         * and the default is 1.0.
         *
         * @param topP The topP setting for prompt execution.
         * @return This builder.
         */
        public Builder withTopP(double topP) {
            if (!Double.isNaN(topP)) {
                settings.put(TOP_P, topP);
            }
            return this;
        }

        /**
         * Set the presence penalty setting for prompt execution. The value is clamped to the range
         * [-2.0, 2.0], and the default is 0.0.
         *
         * @param presencePenalty The presence penalty setting for prompt execution.
         * @return This builder.
         */
        public Builder withPresencePenalty(double presencePenalty) {
            if (!Double.isNaN(presencePenalty)) {
                settings.put(PRESENCE_PENALTY, presencePenalty);
            }
            return this;
        }

        /**
         * Set the frequency penalty setting for prompt execution. The value is clamped to the range
         * [-2.0, 2.0], and the default is 0.0.
         *
         * @param frequencyPenalty The frequency penalty setting for prompt execution.
         * @return This builder.
         */
        public Builder withFrequencyPenalty(double frequencyPenalty) {
            if (!Double.isNaN(frequencyPenalty)) {
                settings.put(FREQUENCY_PENALTY, frequencyPenalty);
            }
            return this;
        }

        /**
         * Set the maximum number of tokens to generate in the output. The value is clamped to the
         * range [1, Integer.MAX_VALUE], and the default is 256.
         *
         * @param maxTokens The maximum number of tokens to generate in the output.
         * @return This builder.
         */
        public Builder withMaxTokens(int maxTokens) {
            settings.put(MAX_TOKENS, maxTokens);
            return this;
        }

        /**
         * Set the number of results to generate for each prompt. The value is clamped to the range
         * [1, Integer.MAX_VALUE], and the default is 1.
         *
         * @param resultsPerPrompt The number of results to generate for each prompt.
         * @return This builder.
         */
        public Builder withResultsPerPrompt(int resultsPerPrompt) {
            settings.put(RESULTS_PER_PROMPT, resultsPerPrompt);
            return this;
        }

        /**
         * Set the best of setting for prompt execution. The value is clamped to the range [1,
         * Integer.MAX_VALUE], and the default is 1.
         *
         * @param bestOf The best of setting for prompt execution.
         * @return This builder.
         */
        public Builder withBestOf(int bestOf) {
            settings.put(BEST_OF, bestOf);
            return this;
        }

        /**
         * Set the user to associate with the prompt execution.
         *
         * @param user The user to associate with the prompt execution.
         * @return This builder.
         */
        public Builder withUser(String user) {
            settings.put(USER, user);
            return this;
        }

        /**
         * Set the stop sequences to use for prompt execution.
         *
         * @param stopSequences The stop sequences to use for prompt execution.
         * @return This builder.
         */
        @SuppressWarnings("unchecked")
        public Builder withStopSequences(List<String> stopSequences) {
            if (stopSequences != null) {
                ((List<String>) settings.computeIfAbsent(STOP_SEQUENCES,
                    k -> new ArrayList<>())).addAll(stopSequences);
            }
            return this;
        }

        /**
         * Set the token selection biases to use for prompt execution. The bias values are clamped
         * to the range [-100, 100].
         *
         * @param tokenSelectionBiases The token selection biases to use for prompt execution.
         * @return This builder.
         */
        @SuppressWarnings("unchecked")
        public Builder withTokenSelectionBiases(Map<Integer, Integer> tokenSelectionBiases) {
            if (tokenSelectionBiases != null) {
                ((Map<Integer, Integer>) settings.computeIfAbsent(TOKEN_SELECTION_BIASES,
                    k -> new HashMap<>())).putAll(tokenSelectionBiases);
            }
            return this;
        }

        /**
         * Build the PromptExecutionSettings.
         *
         * @return A new PromptExecutionSettings from this builder.
         */
        @SuppressWarnings("unchecked")
        public PromptExecutionSettings build() {
            return new PromptExecutionSettings(
                (String) settings.getOrDefault(SERVICE_ID, ""),
                (String) settings.getOrDefault(MODEL_ID, ""),
                (Double) settings.getOrDefault(TEMPERATURE, DEFAULT_TEMPERATURE),
                (Double) settings.getOrDefault(TOP_P, DEFAULT_TOP_P),
                (Double) settings.getOrDefault(PRESENCE_PENALTY, DEFAULT_PRESENCE_PENALTY),
                (Double) settings.getOrDefault(FREQUENCY_PENALTY, DEFAULT_FREQUENCY_PENALTY),
                (Integer) settings.getOrDefault(MAX_TOKENS, DEFAULT_MAX_TOKENS),
                (Integer) settings.getOrDefault(RESULTS_PER_PROMPT, DEFAULT_RESULTS_PER_PROMPT),
                (Integer) settings.getOrDefault(BEST_OF, DEFAULT_BEST_OF),
                (String) settings.getOrDefault(USER, ""),
                (List<String>) settings.getOrDefault(STOP_SEQUENCES, Collections.emptyList()),
                (Map<Integer, Integer>) settings.getOrDefault(TOKEN_SELECTION_BIASES,
                    Collections.emptyMap()));
        }
    }
}
