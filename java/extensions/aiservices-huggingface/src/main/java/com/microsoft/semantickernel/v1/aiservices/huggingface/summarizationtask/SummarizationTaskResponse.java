package com.microsoft.semantickernel.aiservices.huggingface.summarizationtask;

import com.fasterxml.jackson.annotation.JsonProperty;

public interface SummarizationTaskResponse {

    @JsonProperty("score")
    double getScore();

    @JsonProperty("start")
    int getStart();

    @JsonProperty("end")
    int getEnd();

    @JsonProperty("answer")
    String getAnswer();
    
}
