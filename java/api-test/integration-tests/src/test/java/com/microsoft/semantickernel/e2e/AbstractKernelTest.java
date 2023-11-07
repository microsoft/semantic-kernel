// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.memory.VolatileMemoryStore;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;
import org.junit.jupiter.api.condition.EnabledIf;

@EnabledIf("isAzureTestEnabled")
public class AbstractKernelTest {

    public static final String CONF_OPENAI_PROPERTIES = "conf.openai.properties";
    public static final String AZURE_CONF_PROPERTIES = "conf.properties";

    public static Kernel buildTextCompletionKernel() throws ConfigurationException {
        String model = "text-davinci-003";
        final OpenAIAsyncClient openAIClient = getOpenAIClient();
        TextCompletion textCompletion = new OpenAITextCompletion(openAIClient, model);

        return SKBuilders.kernel()
                .withDefaultAIService(textCompletion)
                .withDefaultAIService(
                        SKBuilders.textEmbeddingGeneration()
                                .withOpenAIClient(openAIClient)
                                .withModelId(model)
                                .build())
                .withMemoryStorage(new VolatileMemoryStore())
                .build();
    }

    public static OpenAIAsyncClient getOpenAIClient() throws ConfigurationException {
        return SamplesConfig.getClient();
    }

    public static String getOpenAIModel() throws IOException {
        return getConfigValue(CONF_OPENAI_PROPERTIES, "model");
    }

    public static String getToken(String configName) throws IOException {
        return getConfigValue(configName, "token");
    }

    public static String getEndpoint(String configName) throws IOException {
        return getConfigValue(configName, "endpoint");
    }

    private static String getConfigValue(String configName, String propertyName)
            throws IOException {
        String home = new File(System.getProperty("user.home")).getAbsolutePath();

        try (FileInputStream fis = new FileInputStream(home + "/.oai/" + configName)) {
            Properties props = new Properties();
            props.load(fis);
            String apiKey = props.getProperty(propertyName);
            if (apiKey == null) {
                System.err.println("NO PROPERTY " + propertyName);
                return "";
            }
            return apiKey;
        }
    }

    public static boolean isOpenAIComTestEnabled() {
        return checkConfig(AbstractKernelTest.CONF_OPENAI_PROPERTIES);
    }

    public static boolean isAzureTestEnabled() {
        return checkConfig(AbstractKernelTest.AZURE_CONF_PROPERTIES);
    }

    private static boolean checkConfig(String confOpenaiProperties) {
        if (!Boolean.getBoolean("enable_external_tests")
                && !System.getProperties().containsKey("intellij.debug.agent")) {
            return false;
        }

        try {
            if (AbstractKernelTest.getEndpoint(confOpenaiProperties) == null) {
                System.out.println("Test disabled due to lack of configured azure endpoint");
                return false;
            }

            if (AbstractKernelTest.getToken(confOpenaiProperties) == null) {
                System.out.println("Test disabled due to lack of configured azure token");
                return false;
            }
        } catch (IOException e) {
            return false;
        }

        return true;
    }
}
