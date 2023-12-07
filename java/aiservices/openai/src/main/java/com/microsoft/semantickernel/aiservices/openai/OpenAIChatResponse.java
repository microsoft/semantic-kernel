package com.microsoft.semantickernel.aiservices.openai;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public interface OpenAIChatResponse {

    interface Usage {

        @JsonProperty("prompt_tokens")
        int getPromptTokens();

        @JsonProperty("completion_tokens")
        int getCompletionTokens();

        @JsonProperty("total_tokens")
        int getTotalTokens();
    }

    interface Choice {

        @JsonProperty("message")
        Message getMessage();

        @JsonProperty("finish_details")
        FinishDetails getFinishDetails();

        @JsonProperty("index")
        int getIndex();
    }

    interface Message {

        @JsonProperty("role")
        String getRole();

        @JsonProperty("content")
        String getContent();
    }

    interface FinishDetails {

        @JsonProperty("type")
        String getType();
    }

    @JsonProperty("id")
    String getId();

    @JsonProperty("object")
    String getObject();

    @JsonProperty("created")
    Long getCreated();

    @JsonProperty("model")
    String getModel();

    @JsonProperty("Usage")
    List<Usage> getUsage();

    @JsonProperty("choices")
    List<Choice> getChoices();

}
