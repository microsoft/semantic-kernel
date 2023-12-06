package com.microsoft.semantickernel.aiservices.huggingface.fillmasktask;

import com.fasterxml.jackson.annotation.JsonProperty;

public interface FillMaskTaskResponse {

    @JsonProperty("sequence")
    String getSequence();

    @JsonProperty("score")
    double getScore();

    @JsonProperty("token")
    int getToken();

    @JsonProperty("token_str")
    String getTokenStr();
    
}
