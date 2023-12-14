package com.microsoft.semantickernel.orchestration;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class PromptExecutionSettings {

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
}
