import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import org.springframework.stereotype.Component;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ApplicationContext;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.integration.semantickernel.semanticfunctions.SemanticFunction;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelConfig;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.ComponentScan;

@Configuration
@ComponentScan("org.springframework.integration.semantickernel")
public class SemanticApplication {
    public static void main(String[] args){
        SpringApplication.run(SemanticApplication.class, args);
    }
}
@ConfigurationProperties(prefix = "semantic-kernel")
class SemanticKernelConfiguration {
    private ClientConfig client;
    private SemanticFunctionConfiguration semanticFunction;
    public ClientConfig getClient() {
        return client;
    }
    public void setClient(ClientConfig client) {
        this.client = client;
    }
    public SemanticFunctionConfiguration getSemanticFunction() {
        return semanticFunction;
    }
    public void setSemanticFunction(SemanticFunctionConfiguration semanticFunction) {
        this.semanticFunction = semanticFunction;
    }
    @Data
    @NoArgsConstructor
    public static class ClientConfig {
        private OpenAIConfig openai;
        private

@AutoConfiguration
@EnableConfigurationProperties(Properties.class)
public class AutoConfig {
    @Bean
    public ClientConfig clientConfig() {
        return new ClientConfig();
    }

    @Bean
    public OpenAIConfig openAIConfig() {
        return new OpenAIConfig();
    }

    @Bean
    public AzureOpenAIConfig azureOpenAIConfig() {
        return new AzureOpenAIConfig();
    }

    @Bean
    public SemanticFunctionConfiguration semanticFunctionConfiguration() {
        return new SemanticFunctionConfiguration();
    }

    @Bean
    public SemanticKernelConfiguration semanticKernelConfiguration() {
        return new SemanticKernelConfiguration();
    }

    @Bean
    public SemanticKernelProducer semanticKernelProducer() {
        return new SemanticKernelProducer();
    }

    @Bean
    public SemanticFunctionResource semanticFunctionResource() {
        return new SemanticFunctionResource();
    }

    @Bean
    public SemanticApplication semanticApplication() {
        return new SemanticApplication();
    }
}