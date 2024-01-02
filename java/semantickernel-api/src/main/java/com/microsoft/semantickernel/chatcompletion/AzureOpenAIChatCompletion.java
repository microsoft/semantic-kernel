package com.microsoft.semantickernel.chatcompletion;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.core.credential.TokenCredential;
import com.microsoft.semantickernel.builders.BuildersSingleton;

public interface AzureOpenAIChatCompletion extends ChatCompletionService {
    
    public static Builder builder() {
        return BuildersSingleton.INST.getInstance(Builder.class);
    }

    /**
     * Builder for a ChatCompletionService that uses Azure AI.
     */
    interface Builder extends ChatCompletionService.Builder<AzureOpenAIChatCompletion> {

        /**
         * Sets the API key to use for authentication with the Azure OpenAI service.
         * TokenCredential is given preference over apiKey and endpoint.
         * {@link ChatCompletionService.Builder#withOpenAIAsyncClient(OpenAIAsyncClient) OpenAIClient} is given preference over TokenCredential.
         * @param apiKey the API key to use for authentication with the Azure OpenAI service
         * @return this builder
         */
        Builder withApiKey(String apiKey);

        /**
         * Sets the endpoint to use for authentication with the Azure OpenAI service.
         * TokenCredential is given preference over apiKey and endpoint.
         * {@link ChatCompletionService.Builder#withOpenAIAsyncClient(OpenAIAsyncClient) OpenAIClient} is given preference over TokenCredential.
         * @param endpoint the endpoint to use for authentication with the Azure OpenAI service
         * @return this builder
         */
        Builder withEndpoint(String endpoint);

        /** 
         * Sets the {@link TokenCredential} to use for authentication with the Azure OpenAI service.
         * TokenCredential is given preference over apiKey and endpoint.
         * {@link ChatCompletionService.Builder#withOpenAIAsyncClient(OpenAIAsyncClient) OpenAIClient} is given preference over TokenCredential.
         * @param tokenCredential the {@link TokenCredential} to use for authentication with the Azure OpenAI service
         * @return this builder
         */
        Builder withTokenCredential(TokenCredential   tokenCredential);

    }
    
}
