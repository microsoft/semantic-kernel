// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.huggingface.services;

import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import javax.annotation.Nullable;

public class HuggingFacePromptExecutionSettings extends PromptExecutionSettings {

    @Nullable
    private final Integer topK;
    @Nullable
    private final Double repetitionPenalty;
    @Nullable
    private final Double maxTime;
    @Nullable
    private final Boolean details;
    @Nullable
    private final Boolean logProbs;
    @Nullable
    private final Integer topLogProbs;
    @Nullable
    private final Long seed;

    public HuggingFacePromptExecutionSettings(PromptExecutionSettings copy) {
        super(
            copy.getServiceId(),
            copy.getModelId(),
            copy.getTemperature(),
            copy.getTopP(),
            copy.getPresencePenalty(),
            copy.getFrequencyPenalty(),
            copy.getMaxTokens(),
            copy.getResultsPerPrompt(),
            copy.getBestOf(),
            copy.getUser(),
            copy.getStopSequences(),
            copy.getTokenSelectionBiases(),
            copy.getResponseFormat() == null ? null : copy.getResponseFormat().toString());
        this.topK = null;
        this.repetitionPenalty = null;
        this.maxTime = null;
        this.details = null;
        this.logProbs = null;
        this.topLogProbs = null;
        this.seed = null;
    }

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
     * @param responseFormat       The response format to use for prompt execution
     */
    public HuggingFacePromptExecutionSettings(
        String serviceId,
        String modelId,
        Double temperature,
        Double topP,
        Double presencePenalty,
        Double frequencyPenalty,
        Integer maxTokens,
        Integer resultsPerPrompt,
        Integer bestOf,
        String user,
        @Nullable List<String> stopSequences,
        @Nullable Map<Integer, Integer> tokenSelectionBiases,
        @Nullable String responseFormat,
        @Nullable Integer topK,
        @Nullable Double repetitionPenalty,
        @Nullable Double maxTime,
        @Nullable Boolean details,
        @Nullable Boolean logProbs,
        @Nullable Integer topLogProbs,
        @Nullable Long seed) {
        super(
            serviceId, modelId, temperature, topP, presencePenalty, frequencyPenalty, maxTokens,
            resultsPerPrompt, bestOf, user, stopSequences, tokenSelectionBiases, responseFormat);

        this.topK = topK;
        this.repetitionPenalty = repetitionPenalty;
        this.maxTime = maxTime;
        this.details = details;
        this.logProbs = logProbs;
        this.topLogProbs = topLogProbs;
        this.seed = seed;
    }

    public static HuggingFacePromptExecutionSettings fromExecutionSettings(
        PromptExecutionSettings promptExecutionSettings) {
        if (promptExecutionSettings instanceof HuggingFacePromptExecutionSettings) {
            return (HuggingFacePromptExecutionSettings) promptExecutionSettings;
        }

        return new HuggingFacePromptExecutionSettings(
            promptExecutionSettings.getServiceId(),
            promptExecutionSettings.getModelId(),
            promptExecutionSettings.getTemperature(),
            promptExecutionSettings.getTopP(),
            promptExecutionSettings.getPresencePenalty(),
            promptExecutionSettings.getFrequencyPenalty(),
            promptExecutionSettings.getMaxTokens(),
            promptExecutionSettings.getResultsPerPrompt(),
            promptExecutionSettings.getBestOf(),
            promptExecutionSettings.getUser(),
            promptExecutionSettings.getStopSequences(),
            promptExecutionSettings.getTokenSelectionBiases(),
            promptExecutionSettings.getResponseFormat() != null
                ? promptExecutionSettings.getResponseFormat().toString()
                : null,
            null,
            null,
            null,
            null,
            null,
            null,
            null);
    }

    @Nullable
    public Integer getTopK() {
        return topK;
    }

    @Nullable
    public Double getRepetitionPenalty() {
        return repetitionPenalty;
    }

    @Nullable
    public Double getMaxTime() {
        return maxTime;
    }

    @Nullable
    public Boolean getDetails() {
        return details;
    }

    @Nullable
    public Boolean getLogprobs() {
        return logProbs;
    }

    @Nullable
    public Integer getTopLogProbs() {
        return topLogProbs;
    }

    @Nullable
    public Long getSeed() {
        return seed;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || !(o instanceof HuggingFacePromptExecutionSettings)) {
            return false;
        }
        if (!super.equals(o)) {
            return false;
        }
        HuggingFacePromptExecutionSettings that = (HuggingFacePromptExecutionSettings) o;
        return Objects.equals(topK, that.topK) &&
            Objects.equals(repetitionPenalty, that.repetitionPenalty) &&
            Objects.equals(maxTime, that.maxTime) &&
            Objects.equals(details, that.details) &&
            Objects.equals(logProbs, that.logProbs) &&
            Objects.equals(topLogProbs, that.topLogProbs) &&
            Objects.equals(seed, that.seed);
    }

    @Override
    public int hashCode() {
        return Objects.hash(super.hashCode(), topK, repetitionPenalty, maxTime, details, logProbs,
            topLogProbs, seed);
    }
}
