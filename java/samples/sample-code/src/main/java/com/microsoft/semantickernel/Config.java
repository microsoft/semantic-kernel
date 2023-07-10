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

    public static final String OPENAI_CLIENT_TYPE =
            System.getProperty("OPENAI_CLIENT_TYPE", "OPEN_AI");

    public static OpenAIAsyncClient getClient() throws IOException {
        return ClientType.valueOf(OPENAI_CLIENT_TYPE).getClient();
    }

    public enum ClientType {
        OPEN_AI {
            @Override
            public OpenAIAsyncClient getClient() throws IOException {
                return getClient(CONF_PROPERTIES);
            }

            @Override
            public OpenAIAsyncClient getClient(String file) throws IOException {
                OpenAISettings settings = AIProviderSettings.getOpenAISettingsFromFile(file);

                return new OpenAIClientBuilder()
                        .credential(new NonAzureOpenAIKeyCredential(settings.getKey()))
                        .buildAsyncClient();
            }
        },
        AZURE_OPEN_AI {
            @Override
            public OpenAIAsyncClient getClient() throws IOException {
                return getClient(CONF_PROPERTIES);
            }

            @Override
            public OpenAIAsyncClient getClient(String file)
                    throws IOException {
                AzureOpenAISettings settings = AIProviderSettings.getAzureOpenAISettingsFromFile(file);

                return new OpenAIClientBuilder()
                        .endpoint(settings.getEndpoint())
                        .credential(new AzureKeyCredential(settings.getKey()))
                        .buildAsyncClient();
            }
        };

        public abstract OpenAIAsyncClient getClient() throws IOException;

        /**
         * Returns the client that will handle AzureOpenAI or OpenAI requests.
         *
         * @return client to be used by the kernel.
         */
        public abstract OpenAIAsyncClient getClient(String file) throws IOException;
    }
}
