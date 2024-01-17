package azureopenai;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.microsoft.semantickernel.Kernel;
import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.AutoConfigurations;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;

public class AzureOpenAIAutoConfigurationTest {

  @EnableConfigurationProperties(AzureOpenAiConnectionProperties.class)
  static class TestConfiguration {

  }

  private final ApplicationContextRunner contextRunner = new ApplicationContextRunner().withUserConfiguration(
      TestConfiguration.class).withPropertyValues(
      // @formatter:off
      "client.azureopenai.key=TEST_KEY",
      "client.azureopenai.endpoint=TEST_ENDPOINT",
      "client.azureopenai.deploymentname=TEST_DEPLOYMENT_NAME"
      // @formatter:on
  ).withConfiguration(AutoConfigurations.of(AzureOpenAIAutoConfiguration.class));

  @Test
  public void testSemanticKernel() {
    contextRunner.run(context -> {
      Kernel semanticKernel = context.getBean(Kernel.class);
      assertNotNull(semanticKernel);
    });
  }

}