// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.textcompletion;

import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Settings for a text completion request */
public class CompletionRequestSettings {
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

    public CompletionRequestSettings(
            double temperature,
            double topP,
            double presencePenalty,
            double frequencyPenalty,
            int maxTokens,
            List<String> stopSequences) {
        this.temperature = temperature;
        this.topP = topP;
        this.presencePenalty = presencePenalty;
        this.frequencyPenalty = frequencyPenalty;
        this.maxTokens = maxTokens;
        this.stopSequences = new ArrayList<>(stopSequences);
    }

    public CompletionRequestSettings() {
        this(0, 0, 0, 0, 256, new ArrayList<>());
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="config"></param>
    /// <returns>An instance of <see cref="CompleteRequestSettings"/> </returns>
    public static CompletionRequestSettings fromCompletionConfig(
            PromptTemplateConfig.CompletionConfig config) {
        return new CompletionRequestSettings(
                config.getTemperature(),
                config.getTopP(),
                config.getPresencePenalty(),
                config.getFrequencyPenalty(),
                config.getMaxTokens(),
                new ArrayList<>());
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
}
