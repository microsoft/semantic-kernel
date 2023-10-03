// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;

import java.io.File;
import java.util.List;

/**
 * Helper for creating
 * Refer to the <a href=
 * "https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/samples/sample-code/README.md">
 * README</a> for configuring your environment to run the examples.
 */
public class SamplesConfig {

    public static final List<File> DEFAULT_PROPERTIES_LOCATIONS = List.of(
            new File("java/samples/conf.properties")
    );


    public static OpenAIAsyncClient getClient() throws ConfigurationException {
        return OpenAIClientProvider.getWithAdditional(DEFAULT_PROPERTIES_LOCATIONS);
    }
}
