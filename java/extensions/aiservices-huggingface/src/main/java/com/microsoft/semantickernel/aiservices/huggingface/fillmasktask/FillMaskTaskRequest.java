package com.microsoft.semantickernel.aiservices.huggingface.fillmasktask;

import com.fasterxml.jackson.annotation.JsonProperty;

public interface FillMaskTaskRequest {

    @JsonProperty("inputs")
    String getInputs();
    
}
