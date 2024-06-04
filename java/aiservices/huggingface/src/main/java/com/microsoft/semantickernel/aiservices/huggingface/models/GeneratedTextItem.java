// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.huggingface.models;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import javax.annotation.Nullable;

public class GeneratedTextItem {

    @Nullable
    @JsonProperty("generated_text")
    private final String generatedText;

    @Nullable
    @JsonProperty("details")
    private final TextGenerationDetails details;

    @JsonCreator
    public GeneratedTextItem(
        @JsonProperty("generated_text") @Nullable String generatedText,
        @JsonProperty("details") @Nullable TextGenerationDetails details) {
        this.generatedText = generatedText;
        this.details = details;
    }

    @Nullable
    public String getGeneratedText() {
        return generatedText;
    }

    @Nullable
    public TextGenerationDetails getDetails() {
        return details;
    }

    public static class TextGenerationDetails {

        @Nullable
        @JsonProperty("finish_reason")
        private final String finishReason;

        @JsonProperty("generated_tokens")
        private final int generatedTokens;

        @Nullable
        @JsonProperty("seed")
        private final Long seed;

        @Nullable
        @JsonProperty("prefill")
        private final List<TextGenerationPrefillToken> prefill;

        @Nullable
        @JsonProperty("tokens")
        private final List<TextGenerationToken> tokens;

        @JsonCreator
        public TextGenerationDetails(
            @JsonProperty("finish_reason") @Nullable String finishReason,
            @JsonProperty("generated_tokens") int generatedTokens,
            @JsonProperty("seed") @Nullable Long seed,
            @JsonProperty("prefill") @Nullable List<TextGenerationPrefillToken> prefill,
            @JsonProperty("tokens") @Nullable List<TextGenerationToken> tokens) {
            this.finishReason = finishReason;
            this.generatedTokens = generatedTokens;
            this.seed = seed;
            if (prefill != null) {
                this.prefill = new ArrayList<>(prefill);
            } else {
                this.prefill = null;
            }
            if (tokens != null) {
                this.tokens = new ArrayList<>(tokens);
            } else {
                this.tokens = null;
            }
        }

        @Nullable
        public String getFinishReason() {
            return finishReason;
        }

        public int getGeneratedTokens() {
            return generatedTokens;
        }

        @Nullable
        public Long getSeed() {
            return seed;
        }

        @Nullable
        public List<TextGenerationPrefillToken> getPrefill() {
            return Collections.unmodifiableList(prefill);
        }

        @Nullable
        public List<TextGenerationToken> getTokens() {
            return Collections.unmodifiableList(tokens);
        }
    }

    public static class TextGenerationPrefillToken {

        @JsonProperty("id")
        private final int id;

        @Nullable
        @JsonProperty("text")
        private final String text;

        @JsonProperty("logprob")
        private final double logProb;

        @JsonCreator
        public TextGenerationPrefillToken(
            @JsonProperty("id") int id,
            @JsonProperty("text") @Nullable String text,
            @JsonProperty("logprob") double logProb) {
            this.id = id;
            this.text = text;
            this.logProb = logProb;
        }

        public int getId() {
            return id;
        }

        @Nullable
        public String getText() {
            return text;
        }

        public double getLogProb() {
            return logProb;
        }
    }

    public static class TextGenerationToken extends TextGenerationPrefillToken {

        @JsonProperty("special")
        private final boolean special;

        @JsonCreator
        public TextGenerationToken(
            @JsonProperty("special") boolean special,
            @JsonProperty("id") int id,
            @JsonProperty("text") @Nullable String text,
            @JsonProperty("logprob") double logProb) {
            super(id, text, logProb);
            this.special = special;
        }

        public boolean isSpecial() {
            return special;
        }
    }
}
