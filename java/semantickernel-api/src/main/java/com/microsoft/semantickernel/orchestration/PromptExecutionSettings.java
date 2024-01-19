package com.microsoft.semantickernel.orchestration;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

public class PromptExecutionSettings {

    public static final String DEFAULT_SERVICE_ID = "default";
    public static final int DEFAULT_MAX_TOKENS = 256;
    public static final double DEFAULT_TEMPERATURE = 1.0;
    public static final double DEFAULT_TOP_P = 1.0;
    public static final double DEFAULT_PRESENCE_PENALTY = 0.0;
    public static final double DEFAULT_FREQUENCY_PENALTY = 0.0;
    public static final int DEFAULT_BEST_OF = 1;

    /// <summary>
    /// Service identifier.
    /// This identifies a service and is set when the AI service is registered.
    /// </summary>
    private final String serviceId;

    /// <summary>
    /// Model identifier.
    /// This identifies the AI model these settings are configured for e.g., gpt-4, gpt-3.5-turbo
    /// </summary>
    private final String modelId;

    private final double temperature;

    private final double topP;
    private final double presencePenalty;
    private final double frequencyPenalty;
    private final int maxTokens;
    private final int bestOf;
    private final String user;
    private final List<String> stopSequences;

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>s
    public Map<Integer, Integer> tokenSelectionBiases;

    public PromptExecutionSettings(
        @JsonProperty("service_id") String serviceId,
        @JsonProperty("model_id") String modelId,
        @JsonProperty("temperature") double temperature,
        @JsonProperty("top_p") double topP,
        @JsonProperty("presence_penalty") double presencePenalty,
        @JsonProperty("frequency_penalty") double frequencyPenalty,
        @JsonProperty("max_tokens") int maxTokens,
        @JsonProperty("best_of") int bestOf,
        @JsonProperty("user") String user,
        @JsonProperty(value = "stop_sequences") List<String> stopSequences,
        @JsonProperty(value = "token_selection_biases") Map<Integer, Integer> tokenSelectionBiases) {
        this.serviceId = serviceId;
        this.modelId = modelId;
        this.temperature = temperature;
        this.topP = topP;
        this.presencePenalty = presencePenalty;
        this.frequencyPenalty = frequencyPenalty;
        this.maxTokens = maxTokens;
        this.bestOf = bestOf;
        this.user = user;
        this.stopSequences = stopSequences;
        this.tokenSelectionBiases = tokenSelectionBiases;
    }

    public String getServiceId() {
        return serviceId;
    }

    public String getModelId() {
        return modelId;
    }

    public double getTemperature() {
        return Double.isNaN(temperature) ? DEFAULT_TEMPERATURE : temperature;
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

    public int getBestOf() {
        // TODO: not present in com.azure:azure-ai-openai
        return bestOf;
    }

    public String getUser() {
        return user;
    }

    public List<String> getStopSequences() {
        return stopSequences;
    }

    public Map<Integer, Integer> getTokenSelectionBiases() {
        return tokenSelectionBiases;
    }


    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {

        private String serviceId;
        private String modelId;
        private double temperature = Double.NaN;
        private double topP = Double.NaN;
        private double presencePenalty = Double.NaN;
        private double frequencyPenalty = Double.NaN;
        private int maxTokens = Integer.MIN_VALUE;
        private int bestOf = Integer.MIN_VALUE;
        private String user;
        private List<String> stopSequences;
        public Map<Integer, Integer> tokenSelectionBiases;

        public Builder withServiceId(String serviceId) {
            this.serviceId = serviceId;
            return this;
        }

        public Builder withModelId(String modelId) {
            this.modelId = modelId;
            return this;
        }

        public Builder withTemperature(double temperature) {
            this.temperature = temperature;
            return this;
        }

        public Builder withTopP(double topP) {
            this.topP = topP;
            return this;
        }

        public Builder withPresencePenalty(double presencePenalty) {
            this.presencePenalty = presencePenalty;
            return this;
        }

        public Builder withFrequencyPenalty(double frequencyPenalty) {
            this.frequencyPenalty = frequencyPenalty;
            return this;
        }

        public Builder withMaxTokens(int maxTokens) {
            this.maxTokens = maxTokens;
            return this;
        }

        public Builder withBestOf(int bestOf) {
            this.bestOf = bestOf;
            return this;
        }

        public Builder withUser(String user) {
            this.user = user;
            return this;
        }

        public Builder withStopSequences(List<String> stopSequences) {
            this.stopSequences = stopSequences;
            return this;
        }

        public Builder withTokenSelectionBiases(Map<Integer, Integer> tokenSelectionBiases) {
            this.tokenSelectionBiases = tokenSelectionBiases;
            return this;
        }

        public PromptExecutionSettings build() {
            return new PromptExecutionSettings(
                serviceId,
                modelId,
                Double.isNaN(temperature) ? DEFAULT_TEMPERATURE : temperature,
                Double.isNaN(topP) ? DEFAULT_TOP_P : topP,
                Double.isNaN(presencePenalty) ? DEFAULT_PRESENCE_PENALTY : presencePenalty,
                Double.isNaN(frequencyPenalty) ? DEFAULT_FREQUENCY_PENALTY : frequencyPenalty,
                maxTokens == Integer.MIN_VALUE ? DEFAULT_MAX_TOKENS : maxTokens,
                bestOf == Integer.MIN_VALUE ? DEFAULT_BEST_OF : bestOf,
                user,
                stopSequences,
                tokenSelectionBiases
            );
        }
    }
}
