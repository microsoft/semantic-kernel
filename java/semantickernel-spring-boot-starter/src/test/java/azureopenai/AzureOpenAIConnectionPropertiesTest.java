package azureopenai;

import azureopenai.AzureOpenAIAutoConfigurationTest.TestConfiguration;
import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.AutoConfigurations;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;

import static org.junit.jupiter.api.Assertions.assertNotNull;

public class AzureOpenAIConnectionPropertiesTest {


  private final ApplicationContextRunner contextRunner = new ApplicationContextRunner().withUserConfiguration(
      TestConfiguration.class).withPropertyValues(
      // @formatter:off
      "client.azureopenai.key=TEST_KEY",
      "client.azureopenai.endpoint=TEST_ENDPOINT",
      "client.azureopenai.deploymentname=TEST_DEPLOYMENT_NAME"
      // @formatter:on
  ).withConfiguration(AutoConfigurations.of(AzureOpenAIAutoConfiguration.class));

  @Test
  public void ConnectionPropertiesTest() {
    contextRunner.run(context -> {
      AzureOpenAiConnectionProperties props = context.getBean(AzureOpenAiConnectionProperties.class);
      assertNotNull(props.getEndpoint());
      assertNotNull(props.getKey());
      assertNotNull(props.getDeploymentName());
    });
  }

}
