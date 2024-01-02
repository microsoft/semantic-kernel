package com.microsoft.semantickernel.chatcompletion;

import com.azure.core.credential.TokenCredential;
import com.microsoft.semantickernel.builders.BuildersSingleton;

public interface OpenAIChatCompletion extends ChatCompletionService {
   
    public static Builder builder() {
        return BuildersSingleton.INST.getInstance(Builder.class);
    }

    /**
     * Builder for a ChatCompletionService that uses OpenAI.
     */
    interface Builder extends ChatCompletionService.Builder<OpenAIChatCompletion> {

        /**
         * Sets the API key to use for authentication with the OpenAI service.
         * TokenCredential is given preference over apiKey and endpoint.
         * {@link ChatCompletionService.Builder#withOpenAIAsyncClient(OpenAIAsyncClient) OpenAIClient} is given preference over TokenCredential.
         * @param apiKey the API key to use for authentication with the OpenAI service
         * @return this builder
         */
        Builder withApiKey(String apiKey);

        /**
         * Sets the OpenAI organization id to use for authentication with the OpenAI service.
         * TokenCredential is given preference over apiKey and endpoint.
         * {@link ChatCompletionService.Builder#withOpenAIAsyncClient(OpenAIAsyncClient) OpenAIClient} is given preference over TokenCredential.
         * @param organization the OpenAI organization id to use for authentication with the OpenAI service
         * @return this builder
         */
        Builder withOrganization(String organization);

        /** 
         * Sets the {@link TokenCredential} to use for authentication with the OpenAI service.
         * TokenCredential is given preference over apiKey and endpoint.
         * {@link ChatCompletionService.Builder#withOpenAIAsyncClient(OpenAIAsyncClient) OpenAIClient} is given preference over TokenCredential.
         * @param tokenCredential the {@link TokenCredential} to use for authentication with the OpenAI service
         * @return this builder
         */
        Builder withTokenCredential(TokenCredential   tokenCredential);

    }    
}
