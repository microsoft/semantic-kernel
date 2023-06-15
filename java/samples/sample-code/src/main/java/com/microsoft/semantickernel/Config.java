// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.ai.openai.models.NonAzureOpenAIKeyCredential;
import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.semantickernel.util.AIProviderSettings;
import com.microsoft.semantickernel.util.AzureOpenAISettings;
import com.microsoft.semantickernel.util.OpenAISettings;

import java.io.IOException;

public class Config {

    public static final String CONF_PROPERTIES =
            System.getProperty("CONF_PROPERTIES", "java/samples/conf.properties");

    public enum ClientType {
        OPEN_AI {
            @Override
            public OpenAIAsyncClient getClient() throws IOException {
                OpenAISettings settings = AIProviderSettings.getOpenAISettingsFromFile(CONF_PROPERTIES);
                return new OpenAIClientBuilder()
                        .credential(new NonAzureOpenAIKeyCredential(settings.getKey()))
                        .buildAsyncClient();
            }
        },
        AZURE_OPEN_AI {
            @Override
            public OpenAIAsyncClient getClient()
                    throws IOException {
                AzureOpenAISettings settings = AIProviderSettings.getAzureOpenAISettingsFromFile(CONF_PROPERTIES);

                return new OpenAIClientBuilder()
                        .endpoint(settings.getEndpoint())
                        .credential(new AzureKeyCredential(settings.getKey()))
                        .buildAsyncClient();
            }
        };

        public abstract OpenAIAsyncClient getClient() throws IOException;
    }
}
