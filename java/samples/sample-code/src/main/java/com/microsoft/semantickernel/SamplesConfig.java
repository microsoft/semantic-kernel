// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.connectors.ai.openai.util.OpenAIClientProvider;
import com.microsoft.semantickernel.exceptions.ConfigurationException;

import java.io.File;
import java.util.List;

public class SamplesConfig {

    public static final List<File> DEFAULT_PROPERTIES_LOCATIONS = List.of(
            new File("java/samples/conf.properties")
    );


    public static OpenAIAsyncClient getClient() throws ConfigurationException {
        return OpenAIClientProvider.getWithAdditional(DEFAULT_PROPERTIES_LOCATIONS);
    }
}
