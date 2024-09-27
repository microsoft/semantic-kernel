// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.huggingface.models;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.microsoft.semantickernel.aiservices.huggingface.services.HuggingFacePromptExecutionSettings;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import javax.annotation.Nullable;
import java.util.Arrays;
import java.util.List;

@JsonInclude(Include.NON_NULL)
public class TextGenerationRequest {

    /// <summary>
    /// The input string to generate text for.
    /// </summary>
    @Nullable
    @JsonProperty("inputs")
    private final List<String> inputs;

    /// <summary>
    /// Enable streaming
    /// </summary>
    @JsonProperty("stream")
    private final boolean stream;

    /// <summary>
    /// Parameters used by the model for generation.
    /// </summary>

    @Nullable
    @JsonProperty("parameters")
    private final HuggingFaceTextParameters parameters;

    /// <summary>
    /// Options used by the model for generation.
    /// </summary>
    @Nullable
    @JsonProperty("options")
    private final HuggingFaceTextOptions options;

    public TextGenerationRequest(
        @Nullable String inputs,
        boolean stream,
        @Nullable HuggingFaceTextParameters parameters,
        @Nullable HuggingFaceTextOptions options) {
        this.inputs = Arrays.asList(inputs);
        this.stream = stream;
        this.parameters = parameters;
        this.options = options;
    }

    public static TextGenerationRequest fromPromptAndExecutionSettings(String prompt,
        HuggingFacePromptExecutionSettings executionSettings) {
        return new TextGenerationRequest(
            prompt,
            false,
            new HuggingFaceTextParameters(
                executionSettings.getTopK(),
                executionSettings.getTopP(),
                executionSettings.getTemperature(),
                executionSettings.getRepetitionPenalty(),
                executionSettings.getMaxTokens(),
                executionSettings.getMaxTime(),
                true,
                null,
                null,
                executionSettings.getDetails()),
            new HuggingFaceTextOptions());
    }

    public static class HuggingFaceTextParameters {

        /// <summary>
        /// (Default: None). Number to define the top tokens considered within the sample operation to create new text.
        /// </summary>
        @Nullable
        @JsonProperty("top_k")
        private final Integer topK;

        /// <summary>
        /// (Default: None). Define the tokens that are within the sample operation of text generation.
        /// Add tokens in the sample for more probable to least probable until the sum of the probabilities
        /// is greater than top_p.
        /// </summary>
        @Nullable
        @JsonProperty("top_p")
        private final Double topP;

        /// <summary>
        /// (Default: 1.0). Range (0.0-100.0). The temperature of the sampling operation.
        /// 1 means regular sampling, 0 means always take the highest score,
        /// 100.0 is getting closer to uniform probability.
        /// </summary>
        @Nullable
        @JsonProperty("temperature")
        private final Double temperature;

        /// <summary>
        /// (Default: None). (0.0-100.0). The more a token is used within generation
        /// the more it is penalized to not be picked in successive generation passes.
        /// </summary>
        @Nullable
        @JsonProperty("repetition_penalty")
        private final Double repetitionPenalty;

        /// <summary>
        /// (Default: None). Range (0-250). The amount of new tokens to be generated,
        /// this does not include the input length it is a estimate of the size of generated text you want.
        /// Each new tokens slows down the request, so look for balance between response times
        /// and length of text generated.
        /// </summary>
        @Nullable
        @JsonProperty("max_new_tokens")
        private final Integer maxNewTokens;

        /// <summary>
        /// (Default: None). Range (0-120.0). The amount of time in seconds that the query should take maximum.
        /// Network can cause some overhead so it will be a soft limit.
        /// Use that in combination with max_new_tokens for best results.
        /// </summary>
        @Nullable
        @JsonProperty("max_time")
        private final Double maxTime;

        /// <summary>
        /// (Default: True). If set to False, the return results will not contain the original query making it easier for prompting.
        /// </summary>
        @JsonProperty("return_full_text")
        private final boolean returnFullText;

        /// <summary>
        /// (Default: 1). The number of proposition you want to be returned.
        /// </summary>
        @Nullable
        @JsonProperty("num_return_sequences")
        private final Integer numReturnSequences;

        /// <summary>
        /// (Optional: True). Whether or not to use sampling, use greedy decoding otherwise.
        /// </summary>
        @Nullable
        @JsonProperty("do_sample")
        private final Boolean doSample;

        /// <summary>
        /// (Optional: True) Whether or not to include the details of the generation.
        /// </summary>
        /// <remarks>
        /// Disabling this won't provide information about token usage.
        /// </remarks>
        @Nullable
        @JsonProperty("details")
        private final Boolean details;

        public static class Builder {
            @JsonProperty("top_k") @Nullable Integer topK,
            @JsonProperty("top_p") @Nullable Double topP,
            @JsonProperty("temperature") @Nullable Double temperature,
            @JsonProperty("repetition_penalty") @Nullable Double repetitionPenalty,
            @JsonProperty("max_new_tokens") @Nullable Integer maxNewTokens,
            @JsonProperty("max_time") @Nullable Double maxTime,
            @JsonProperty("return_full_text") boolean returnFullText,
            @JsonProperty("num_return_sequences") @Nullable Integer numReturnSequences,
            @JsonProperty("do_sample") @Nullable Boolean doSample,
            @JsonProperty("details") @Nullable Boolean details) {
            this.topK = topK;
            this.topP = topP;
            this.temperature = temperature;
            this.repetitionPenalty = repetitionPenalty;
            this.maxNewTokens = maxNewTokens;
            this.maxTime = maxTime;
            this.returnFullText = returnFullText;
            this.numReturnSequences = numReturnSequences;
            this.doSample = doSample;
            this.details = details;
        }

        @Nullable
        public Integer getTopK() {
            return topK;
        }

        @Nullable
        public Double getTopP() {
            return topP;
        }

        @Nullable
        public Double getTemperature() {
            return temperature;
        }

        @Nullable
        public Double getRepetitionPenalty() {
            return repetitionPenalty;
        }

        @Nullable
        public Integer getMaxNewTokens() {
            return maxNewTokens;
        }

        @Nullable
        public Double getMaxTime() {
            return maxTime;
        }

        public boolean isReturnFullText() {
            return returnFullText;
        }

        @Nullable
        public Integer getNumReturnSequences() {
            return numReturnSequences;
        }

        @Nullable
        public Boolean getDoSample() {
            return doSample;
        }

        @Nullable
        public Boolean getDetails() {
            return details;
        }
    }

    @SuppressFBWarnings("SS_SHOULD_BE_STATIC")
    public static class HuggingFaceTextOptions {

        /// <summary>
        /// (Default: true). There is a cache layer on the inference API to speedup requests we have already seen.
        /// Most models can use those results as is as models are deterministic (meaning the results will be the same anyway).
        /// However if you use a non deterministic model, you can set this parameter to prevent the caching mechanism from being
        /// used resulting in a real new query.
        /// </summary>
        @JsonProperty("use_cache")
        private final boolean useCache = true;

        /// <summary>
        /// (Default: false) If the model is not ready, wait for it instead of receiving 503.
        /// It limits the number of requests required to get your inference done.
        /// It is advised to only set this flag to true after receiving a 503 error as it will limit hanging in your application to known places.
        /// </summary>
        @JsonProperty("wait_for_model")
        private final boolean waitForModel = false;

        public boolean isUseCache() {
            return useCache;
        }

        public boolean isWaitForModel() {
            return waitForModel;
        }
    }
}
