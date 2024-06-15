package com.microsoft.semantickernel.azureopenai;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.microsoft.semantickernel.starter.AzureOpenAIConnectionProperties;
import com.microsoft.semantickernel.starter.SemanticKernelAutoConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.AutoConfigurations;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.test.context.ActiveProfiles;

@ActiveProfiles("test")
public class AzureOpenAIConnectionPropertiesTest {

    ApplicationContextRunner contextRunner =
            new ApplicationContextRunner()
                    .withPropertyValues(
                            // @formatter:off
                            "client.azureopenai.key=TEST_KEY",
                            "client.azureopenai.endpoint=TEST_ENDPOINT",
                            "client.azureopenai.deploymentname=TEST_DEPLOYMENT_NAME"

                            // @formatter:on
                            )
                    .withConfiguration(
                            AutoConfigurations.of(SemanticKernelAutoConfiguration.class));

    @Test
    public void ConnectionPropertiesTest() {
        contextRunner.run(
                context -> {
                    AzureOpenAIConnectionProperties props =
                            context.getBean(AzureOpenAIConnectionProperties.class);
                    assertNotNull(props.getEndpoint());
                    assertNotNull(props.getKey());
                    assertNotNull(props.getDeploymentName());
                });
    }
}
