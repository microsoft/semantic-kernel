package com.microsoft.semantickernel.aiservices.huggingface.texttoimagetask;

import com.fasterxml.jackson.annotation.JsonProperty;

public interface TextToImageTaskRequest {

    @JsonProperty("inputs")
    String getInputs();
}
