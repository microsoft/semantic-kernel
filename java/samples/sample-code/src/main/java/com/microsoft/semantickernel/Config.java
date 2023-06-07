package com.microsoft.semantickernel;

import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.openai.AzureOpenAIClient;
import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.openai.OpenAIClientBuilder;
import com.microsoft.semantickernel.util.AzureOpenAISettings;
import com.microsoft.semantickernel.util.AIProviderSettings;
import com.microsoft.semantickernel.util.OpenAISettings;

import java.io.IOException;

public class Config {

    public static final String CONF_PROPERTIES =
            System.getProperty("CONF_PROPERITES", "java/samples/conf.properties");

    public enum ClientType {
        OPEN_AI {
            @Override
            public OpenAIAsyncClient getClient() throws IOException {
                OpenAISettings settings = AIProviderSettings.getOpenAISettingsFromFile(CONF_PROPERTIES);
                return new OpenAIClientBuilder()
                        .setApiKey(settings.getKey())
                        .build();
            }
        },
        AZURE_OPEN_AI {
            @Override
            public OpenAIAsyncClient getClient()
                 throws IOException {
                    AzureOpenAISettings settings = AIProviderSettings.getAzureOpenAISettingsFromFile(CONF_PROPERTIES);

                    return new AzureOpenAIClient(
                            new com.azure.ai.openai.OpenAIClientBuilder()
                                    .endpoint(settings.getEndpoint())
                                    .credential(new AzureKeyCredential(settings.getKey()))
                                    .buildAsyncClient());
            }
        };

        public abstract OpenAIAsyncClient getClient() throws IOException;
    }
}
