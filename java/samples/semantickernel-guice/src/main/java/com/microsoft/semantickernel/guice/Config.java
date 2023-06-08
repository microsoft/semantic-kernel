// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.guice;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.ai.openai.models.NonAzureOpenAIKeyCredential;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

// TODO Remove when the upstream configuration updates arrive
public class Config {

    private static final Logger LOGGER = LoggerFactory.getLogger(Config.class);

    public static final String OPEN_AI_CONF_PROPERTIES = "samples/java/semantickernel-samples/conf.openai.properties";
    public static final String AZURE_CONF_PROPERTIES = "samples/java/semantickernel-samples/conf.azure.properties";

    public static String getOpenAIKey(String conf) {
        return getConfigValue(conf, "token");
    }

    public static String getAzureOpenAIEndpoint(String conf) {
        return getConfigValue(conf, "endpoint");
    }

    private static String getConfigValue(String configFile, String propertyName) {
        File config = new File(configFile);
        try (FileInputStream fis = new FileInputStream(config.getAbsolutePath())) {
            Properties props = new Properties();
            props.load(fis);
            return props.getProperty(propertyName);
        } catch (IOException e) {
            LOGGER.error(
                    "Unable to load config value " + propertyName + " from file" + configFile, e);
            throw new RuntimeException(configFile + " not configured properly");
        }
    }

    /**
     * Returns the client that will handle AzureOpenAI or OpenAI requests.
     *
     * @param useAzureOpenAI whether to use AzureOpenAI or OpenAI.
     * @return client to be used by the kernel.
     */
    public static OpenAIAsyncClient getClient(boolean useAzureOpenAI) {
        if (useAzureOpenAI) {
            return new OpenAIClientBuilder()
                    .endpoint(Config.getAzureOpenAIEndpoint(AZURE_CONF_PROPERTIES))
                    .credential(new AzureKeyCredential(Config.getOpenAIKey(AZURE_CONF_PROPERTIES)))
                    .buildAsyncClient();
        }

        return new OpenAIClientBuilder()
                .credential(new NonAzureOpenAIKeyCredential(Config.getOpenAIKey(OPEN_AI_CONF_PROPERTIES)))
                .buildAsyncClient();
    }
}
