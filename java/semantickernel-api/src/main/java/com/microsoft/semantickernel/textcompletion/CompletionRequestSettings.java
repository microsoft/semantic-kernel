// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.ai.AIRequestSettings;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Settings for a text completion request */
public class CompletionRequestSettings extends AIRequestSettings implements Buildable {

    /**
     * Temperature controls the randomness of the completion. The higher the temperature, the more
     * random the completion
     */
    private final double temperature; // { get; set; } = 0;

    /**
     * TopP controls the diversity of the completion. The higher the TopP, the more diverse the
     * completion.
     */
    private final double topP; // { get; set; } = 0;

    /**
     * Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear
     * in the text so far, increasing the model's likelihood to talk about new topics.
     */
    private final double presencePenalty; // { get; set; } = 0;

    /**
     * Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing
     * frequency in the text so far, decreasing the model's likelihood to repeat the same line
     * verbatim.
     */
    private final double frequencyPenalty; // { get; set; } = 0;

    /** The maximum number of tokens to generate in the completion. */
    private final int maxTokens; // { get; set; } = 256;

    /** Sequences where the completion will stop generating further tokens. */
    private final List<String> stopSequences; // { get; set; } = Array.Empty<string>();

    /**
     * The maximum number of completions to generate for each prompt. This is used by the
     * CompletionService to generate multiple completions for a single prompt.
     */
    private final int bestOf;

    /**
     * A unique identifier representing your end-user, which can help OpenAI to monitor and detect
     * abuse
     */
    private final String user;

    /**
     * Create a new settings object with the given values.
     *
     * @param temperature Temperature controls the randomness of the completion.
     * @param topP TopP controls the diversity of the completion.
     * @param presencePenalty Number between -2.0 and 2.0. Positive values penalize new tokens based
     *     on whether they appear in the text so far, increasing the model's likelihood to talk
     *     about new topics.
     * @param frequencyPenalty Number between -2.0 and 2.0. Positive values penalize new tokens
     *     based on their existing frequency in the text so far, decreasing the model's likelihood
     *     to repeat the same line verbatim.
     * @param maxTokens The maximum number of tokens to generate in the completion.
     */
    public CompletionRequestSettings(
            double temperature,
            double topP,
            double presencePenalty,
            double frequencyPenalty,
            int maxTokens) {
        this(
                temperature,
                topP,
                presencePenalty,
                frequencyPenalty,
                maxTokens,
                1,
                "",
                Collections.emptyList(),
                null,
                null);
    }

    /**
     * Create a new settings object with the given values.
     *
     * @param temperature Temperature controls the randomness of the completion.
     * @param topP TopP controls the diversity of the completion.
     * @param presencePenalty Number between -2.0 and 2.0. Positive values penalize new tokens based
     *     on whether they appear in the text so far, increasing the model's likelihood to talk
     *     about new topics.
     * @param frequencyPenalty Number between -2.0 and 2.0. Positive values penalize new tokens
     *     based on their existing frequency in the text so far, decreasing the model's likelihood
     *     to repeat the same line verbatim.
     * @param maxTokens The maximum number of tokens to generate in the completion.
     * @param bestOf The maximum number of completions to generate for each prompt. This is used by
     *     the CompletionService to generate multiple completions for a single prompt.
     * @param user A unique identifier representing your end-user, which can help OpenAI to monitor
     *     and detect abuse
     * @param stopSequences Sequences where the completion will stop generating further tokens.
     */
    public CompletionRequestSettings(
            @JsonProperty("temperature") double temperature,
            @JsonProperty("top_p") double topP,
            @JsonProperty("presence_penalty") double presencePenalty,
            @JsonProperty("frequency_penalty") double frequencyPenalty,
            @JsonProperty("max_tokens") int maxTokens,
            @JsonProperty("best_of") int bestOf,
            @JsonProperty("user") String user,
            @JsonProperty(value = "stop_sequences") List<String> stopSequences,
            @JsonProperty(value = "service_id") @Nullable String serviceId,
            @JsonProperty(value = "model_id") @Nullable String modelId) {
        super(serviceId, modelId);
        this.temperature = temperature;
        this.topP = topP;
        this.presencePenalty = presencePenalty;
        this.frequencyPenalty = frequencyPenalty;
        this.maxTokens = maxTokens;

        // bestOf must be at least 1
        this.bestOf = Math.max(1, bestOf);

        if (user == null) {
            user = "";
        }
        this.user = user;
        if (stopSequences == null) {
            stopSequences = new ArrayList<>();
        }
        this.stopSequences = stopSequences;
    }

    /** Create a new settings object with default values. */
    public CompletionRequestSettings() {
        this(0, 0, 0, 0, 256, 1, "", new ArrayList<>(), null, null);
    }

    public CompletionRequestSettings(@Nonnull CompletionRequestSettings requestSettings) {
        this(
                requestSettings.getTemperature(),
                requestSettings.getTopP(),
                requestSettings.getPresencePenalty(),
                requestSettings.getFrequencyPenalty(),
                requestSettings.getMaxTokens(),
                requestSettings.getBestOf(),
                requestSettings.getUser(),
                requestSettings.getStopSequences(),
                requestSettings.getServiceId(),
                requestSettings.getModelId());
    }

    /**
     * Temperature controls the randomness of the completion. The higher the temperature, the more
     * random the completion
     */
    public double getTemperature() {
        return temperature;
    }

    /**
     * TopP controls the diversity of the completion. The higher the TopP, the more diverse the
     * completion.
     */
    public double getTopP() {
        return topP;
    }

    /**
     * Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear
     * in the text so far, increasing the model's likelihood to talk about new topics.
     */
    public double getPresencePenalty() {
        return presencePenalty;
    }

    /**
     * Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing
     * frequency in the text so far, decreasing the model's likelihood to repeat the same line
     * verbatim.
     */
    public double getFrequencyPenalty() {
        return frequencyPenalty;
    }

    /** The maximum number of tokens to generate in the completion. */
    public int getMaxTokens() {
        return maxTokens;
    }

    /** Sequences where the completion will stop generating further tokens. */
    public List<String> getStopSequences() {
        return Collections.unmodifiableList(stopSequences);
    }

    /**
     * The maximum number of completions to generate for each prompt. This is used by the
     * CompletionService to generate multiple completions for a single prompt.
     */
    public Integer getBestOf() {
        return bestOf;
    }

    /**
     * A unique identifier representing your end-user, which can help OpenAI to monitor and detect
     * abuse
     */
    public String getUser() {
        return user;
    }

    /** Builder for CompletionRequestSettings */
    public static class Builder implements SemanticKernelBuilder<CompletionRequestSettings> {

        private final CompletionRequestSettings completionConfig;

        public Builder() {
            completionConfig = new CompletionRequestSettings();
        }

        public Builder(CompletionRequestSettings completionConfig) {
            this.completionConfig = completionConfig;
        }

        public Builder temperature(double temperature) {
            return new Builder(
                    new CompletionRequestSettings(
                            temperature,
                            completionConfig.topP,
                            completionConfig.presencePenalty,
                            completionConfig.frequencyPenalty,
                            completionConfig.maxTokens,
                            completionConfig.bestOf,
                            completionConfig.user,
                            completionConfig.stopSequences,
                            completionConfig.getServiceId(),
                            completionConfig.getModelId()));
        }

        public Builder topP(double topP) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            topP,
                            completionConfig.presencePenalty,
                            completionConfig.frequencyPenalty,
                            completionConfig.maxTokens,
                            completionConfig.bestOf,
                            completionConfig.user,
                            completionConfig.stopSequences,
                            completionConfig.getServiceId(),
                            completionConfig.getModelId()));
        }

        public Builder presencePenalty(double presencePenalty) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            completionConfig.topP,
                            presencePenalty,
                            completionConfig.frequencyPenalty,
                            completionConfig.maxTokens,
                            completionConfig.bestOf,
                            completionConfig.user,
                            completionConfig.stopSequences,
                            completionConfig.getServiceId(),
                            completionConfig.getModelId()));
        }

        public Builder frequencyPenalty(double frequencyPenalty) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            completionConfig.topP,
                            completionConfig.presencePenalty,
                            frequencyPenalty,
                            completionConfig.maxTokens,
                            completionConfig.bestOf,
                            completionConfig.user,
                            completionConfig.stopSequences,
                            completionConfig.getServiceId(),
                            completionConfig.getModelId()));
        }

        public Builder maxTokens(int maxTokens) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            completionConfig.topP,
                            completionConfig.presencePenalty,
                            completionConfig.frequencyPenalty,
                            maxTokens,
                            completionConfig.bestOf,
                            completionConfig.user,
                            completionConfig.stopSequences,
                            completionConfig.getServiceId(),
                            completionConfig.getModelId()));
        }

        public Builder bestOf(int bestOf) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            completionConfig.topP,
                            completionConfig.presencePenalty,
                            completionConfig.frequencyPenalty,
                            completionConfig.maxTokens,
                            bestOf,
                            completionConfig.user,
                            completionConfig.stopSequences,
                            completionConfig.getServiceId(),
                            completionConfig.getModelId()));
        }

        public Builder user(String user) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            completionConfig.topP,
                            completionConfig.presencePenalty,
                            completionConfig.frequencyPenalty,
                            completionConfig.maxTokens,
                            completionConfig.bestOf,
                            user,
                            completionConfig.stopSequences,
                            completionConfig.getServiceId(),
                            completionConfig.getModelId()));
        }

        public Builder stopSequences(List<String> stopSequences) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            completionConfig.topP,
                            completionConfig.presencePenalty,
                            completionConfig.frequencyPenalty,
                            completionConfig.maxTokens,
                            completionConfig.bestOf,
                            completionConfig.user,
                            stopSequences,
                            completionConfig.getServiceId(),
                            completionConfig.getModelId()));
        }

        public Builder serviceId(String serviceId) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            completionConfig.topP,
                            completionConfig.presencePenalty,
                            completionConfig.frequencyPenalty,
                            completionConfig.maxTokens,
                            completionConfig.bestOf,
                            completionConfig.user,
                            completionConfig.stopSequences,
                            serviceId,
                            completionConfig.getModelId()));
        }

        public Builder modelId(String modelId) {
            return new Builder(
                    new CompletionRequestSettings(
                            completionConfig.temperature,
                            completionConfig.topP,
                            completionConfig.presencePenalty,
                            completionConfig.frequencyPenalty,
                            completionConfig.maxTokens,
                            completionConfig.bestOf,
                            completionConfig.user,
                            completionConfig.stopSequences,
                            completionConfig.getServiceId(),
                            modelId));
        }

        public CompletionRequestSettings build() {
            return completionConfig;
        }
    }
}
