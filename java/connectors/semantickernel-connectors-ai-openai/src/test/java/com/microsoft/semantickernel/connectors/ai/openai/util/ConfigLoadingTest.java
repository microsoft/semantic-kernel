// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.connectors.ai.openai.util;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

public class ConfigLoadingTest {

    @Test
    public void openAiConfigIsLoaded() throws ConfigurationException, IOException {
        List<String> entries = Arrays.asList("client.openai.key: 123");

        OpenAIAsyncClient client = runWithConfig(entries);
        Assertions.assertNotNull(client);
    }

    @Test
    public void azureOpenAiConfigIsLoaded() throws ConfigurationException, IOException {
        List<String> entries =
                Arrays.asList(
                        "client.azureopenai.key: 123",
                        "client.azureopenai.endpoint: https://endpoint");

        OpenAIAsyncClient client = runWithConfig(entries);
        Assertions.assertNotNull(client);
    }

    private static OpenAIAsyncClient runWithConfig(List<String> entries)
            throws IOException, ConfigurationException {
        Path dir = Files.createTempDirectory("testConfig");
        File props = createConfig(dir, entries);
        return OpenAIClientProvider.get(Arrays.asList(props));
    }

    private static File createConfig(Path dir, List<String> entries) throws IOException {
        File props = Files.createTempFile(dir, "a", ".properties").toFile();

        try (FileWriter fos = new FileWriter(props)) {
            entries.forEach(
                    e -> {
                        try {
                            fos.write(e + System.lineSeparator());
                        } catch (IOException ioException) {
                            ioException.printStackTrace();
                        }
                    });
        }
        return props;
    }
}
