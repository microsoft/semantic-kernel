package com.microsoft.semantickernel;

import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.openai.AzureOpenAIClient;
import com.microsoft.openai.OpenAIAsyncClient;
import com.microsoft.openai.OpenAIClientBuilder;
import com.microsoft.semantickernel.util.Settings;

import java.io.IOException;

public class Config {

    public static final String CONF_PROPERTIES = "samples/java/semantickernel-samples/conf.properties";

    /**
     * Returns the client that will handle AzureOpenAI or OpenAI requests.
     *
     * @param useAzureOpenAI whether to use AzureOpenAI or OpenAI.
     * @return client to be used by the kernel.
     */
    public static OpenAIAsyncClient getClient(boolean useAzureOpenAI) throws IOException {
        if (useAzureOpenAI) {
            Settings.AzureOpenAISettings settings = Settings.getAzureOpenAISettingsFromFile(CONF_PROPERTIES);

            return new AzureOpenAIClient(
                    new com.azure.ai.openai.OpenAIClientBuilder()
                            .endpoint(settings.getEndpoint())
                            .credential(new AzureKeyCredential(settings.getKey()))
                            .buildAsyncClient());
        }

        Settings.OpenAISettings settings = Settings.getOpenAISettingsFromFile(CONF_PROPERTIES);
        return new OpenAIClientBuilder()
                .setApiKey(settings.getKey())
                .build();
    }
}
