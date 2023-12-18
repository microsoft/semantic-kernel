package com.microsoft.semantickernel.orchestration;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class PromptExecutionSettings {

    public static final int DEFAULT_MAX_TOKENS = 256;

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
        @JsonProperty(value = "stop_sequences") List<String> stopSequences) {
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
    }

    public String getServiceId() {
        return serviceId;
    }

    public String getModelId() {
        return modelId;
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

    public int getBestOf() {
        return bestOf;
    }

    public String getUser() {
        return user;
    }

    public List<String> getStopSequences() {
        return stopSequences;
    }


    public static class Builder {

        private String serviceId;
        private String modelId;
        private double temperature;
        private double topP;
        private double presencePenalty;
        private double frequencyPenalty;
        private int maxTokens;
        private int bestOf;
        private String user;
        private List<String> stopSequences;

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

        public PromptExecutionSettings build() {
            return new PromptExecutionSettings(serviceId, modelId, temperature, topP,
                presencePenalty, frequencyPenalty, maxTokens, bestOf, user, stopSequences);
        }
    }
}
