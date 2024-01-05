
import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.util.Assert;

@AutoConfiguration
@EnableConfigurationProperties(AzureOpenAiConnectionProperties.class)
public class AzureOpenAIAutoConfiguration {

  @Bean
  @ConditionalOnClass(OpenAIClientBuilder.class)
  @ConditionalOnMissingBean
  public OpenAIClient openAIClient(AzureOpenAiConnectionProperties connectionProperties) {
    Assert.hasText(connectionProperties.getEndpoint(), "Azure OpenAI endpoint must be set");
    Assert.hasText(connectionProperties.getKey(), "Azure OpenAI key must be set");
    return new OpenAIClientBuilder().endpoint(connectionProperties.getEndpoint())
        .credential(new AzureKeyCredential(connectionProperties.getKey()))
        .buildClient();
  }

  @Bean
  @ConditionalOnClass(OpenAIAsyncClient.class)
  public OpenAIAsyncClient openAIAsyncClient(AzureOpenAiConnectionProperties connectionProperties) {
    Assert.hasText(connectionProperties.getEndpoint(), "Azure OpenAI endpoint must be set");
    Assert.hasText(connectionProperties.getKey(), "Azure OpenAI key must be set");
    return new OpenAIClientBuilder().endpoint(connectionProperties.getEndpoint())
        .credential(new AzureKeyCredential(connectionProperties.getKey()))
        .buildAsyncClient();
  }

  @Bean
  public Kernel semanticKernel(AzureOpenAiConnectionProperties connectionProperties) {
    Assert.hasText(connectionProperties.getDeploymentName(),
        "Azure OpenAI deployment name must be set and match the ModelID");
    OpenAIAsyncClient openAIAsyncClient = openAIAsyncClient(new AzureOpenAiConnectionProperties());
    ChatCompletion<ChatHistory> chatCompletion = SKBuilders.chatCompletion()
        .withOpenAIClient(openAIAsyncClient)
        .withModelId(connectionProperties.getDeploymentName())
        .build();
    return SKBuilders.kernel().withDefaultAIService(chatCompletion).build();
  }

}