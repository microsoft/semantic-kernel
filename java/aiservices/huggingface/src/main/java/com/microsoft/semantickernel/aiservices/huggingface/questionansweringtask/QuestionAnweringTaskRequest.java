package com.microsoft.semantickernel.aiservices.huggingface.questionansweringtask;

import com.fasterxml.jackson.annotation.JsonProperty;

public interface QuestionAnweringTaskRequest {
   
    interface QuestionAnsweringTaskInputs {
        
        @JsonProperty("question")
        String getQuestion();
        
        @JsonProperty("context")
        String getContext();
    }

    @JsonProperty("inputs")
    QuestionAnsweringTaskInputs getInputs();
    
}
