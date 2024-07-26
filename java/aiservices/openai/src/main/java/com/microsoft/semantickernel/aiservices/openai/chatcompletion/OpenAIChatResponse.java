// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.aiservices.openai.chatcompletion;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Represents the response from the OpenAI chat completion API.
 */
public interface OpenAIChatResponse {

    /**
     * Represents the usage of the chat completion API.
     */
    interface Usage {

        /**
         * Gets the number of tokens used for the prompt.
         *
         * @return the number of tokens used for the prompt
         */
        @JsonProperty("prompt_tokens")
        int getPromptTokens();

        /**
         * Gets the number of tokens used for the completion.
         *
         * @return the number of tokens used for the completion
         */
        @JsonProperty("completion_tokens")
        int getCompletionTokens();

        /**
         * Gets the total number of tokens used.
         *
         * @return the total number of tokens used
         */
        @JsonProperty("total_tokens")
        int getTotalTokens();
    }

    /**
     * Represents a choice in the chat completion response.
     */
    interface Choice {

        /**
         * Gets the message in the chat completion response.
         *
         * @return the message in the chat completion response
         */
        @JsonProperty("message")
        Message getMessage();

        /**
         * Gets the finish details in the chat completion response.
         *
         * @return the finish details in the chat completion response
         */
        @JsonProperty("finish_details")
        FinishDetails getFinishDetails();

        /**
         * Gets the index of the choice.
         *
         * @return the index of the choice
         */
        @JsonProperty("index")
        int getIndex();
    }

    /**
     * Represents a message in the chat completion response.
     */
    interface Message {

        /**
         * Gets the role of the message.
         *
         * @return the role of the message
         */
        @JsonProperty("role")
        String getRole();

        /**
         * Gets the content of the message.
         *
         * @return the content of the message
         */
        @JsonProperty("content")
        String getContent();
    }

    /**
     * Represents the finish details in the chat completion response.
     */
    interface FinishDetails {

        /**
         * Gets the type of the finish details.
         *
         * @return the type of the finish details
         */
        @JsonProperty("type")
        String getType();
    }

    /**
     * Gets the id of the chat completion response.
     *
     * @return the id of the chat completion response
     */
    @JsonProperty("id")
    String getId();

    /**
     * Gets the object of the chat completion response.
     *
     * @return the object of the chat completion response
     */
    @JsonProperty("object")
    String getObject();

    /**
     * Gets the created time of the chat completion response.
     *
     * @return the created time of the chat completion response
     */
    @JsonProperty("created")
    Long getCreated();

    /**
     * Gets the model of the chat completion response.
     *
     * @return the model of the chat completion response
     */
    @JsonProperty("model")
    String getModel();

    /**
     * Gets the usage of the chat completion response.
     *
     * @return the usage of the chat completion response
     */
    @JsonProperty("Usage")
    List<Usage> getUsage();

    /**
     * Gets the choices of the chat completion response.
     *
     * @return the choices of the chat completion response
     */
    @JsonProperty("choices")
    List<Choice> getChoices();

}
