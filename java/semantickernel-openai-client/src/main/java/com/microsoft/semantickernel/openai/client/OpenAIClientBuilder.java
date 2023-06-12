// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.openai.client;

/** Builds an OpenAIClient for use with <a href="https://api.openai.com/v1">api.openai.com/v1</a> */
public final class OpenAIClientBuilder {
    private String endpoint = "https://api.openai.com/v1";
    private String apiKey;

    public OpenAIClientBuilder setApiKey(String apiKey) {
        this.apiKey = apiKey;
        return this;
    }

    public OpenAIClientBuilder setEndpoint(String endpoint) {
        this.endpoint = endpoint;
        return this;
    }

    public OpenAIAsyncClient build() {
        return new OpenAIAsyncClientImpl(endpoint, apiKey);
    }
}
