// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.azureopenai;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.starter.AzureOpenAIConnectionProperties;
import com.microsoft.semantickernel.starter.SemanticKernelAutoConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.AutoConfigurations;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;

@EnableConfigurationProperties(AzureOpenAIConnectionProperties.class)
@SpringBootTest(classes = SemanticKernelAutoConfiguration.class)
public class SemanticKernelAutoConfigurationTest {

    @Autowired
    Kernel kernel;

    @Test
    public void testSemanticKernelAutoConfig() {
        ApplicationContextRunner runner = new ApplicationContextRunner();
        runner.withPropertyValues(
        // @formatter:off
            "client.azureopenai.key=TEST_KEY",
            "client.azureopenai.endpoint=TEST_ENDPOINT"
            // @formatter:on
        );
        runner.withConfiguration(AutoConfigurations.of(SemanticKernelAutoConfiguration.class));
        runner.run(
            context -> {
                assertNotNull(kernel);
            });
    }
}
