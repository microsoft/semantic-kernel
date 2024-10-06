package com.microsoft.semantickernel.aiservices.ollama;

import java.time.ZonedDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

interface OllamaResponseModel {
  
    @JsonProperty("model")
    String getModel();

    @JsonProperty("created_at")
    ZonedDateTime getCreatedAt();

    @JsonProperty("response")
    String getResponse();

    @JsonProperty("done")
    boolean getDone();

    @JsonProperty("total_duration")
    long getTotalDuration();

    @JsonProperty("load_duration")
    long getLoadDuration();

    @JsonProperty("prompt_eval_count")
    int getPromptEvalCount();

    @JsonProperty("prompt_eval_duration")
    long getPromptEvalDuration();

    @JsonProperty("eval_count")
    int getEvalCount();

    @JsonProperty("eval_duration")
    long getEvalDuration();

}
