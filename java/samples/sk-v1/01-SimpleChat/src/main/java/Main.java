import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Map;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelResult;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunction;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplateEngine;

public class Main {
    
    final static String GPT_35_DEPLOYMENT_NAME = System.getenv("GPT_35_DEPLOYMENT_NAME");
    final static String GPT_4_DEPLOYMENT_NAME = System.getenv("GPT_4_DEPLOYMENT_NAME");
    final static String AZURE_OPENAI_ENDPOINT = System.getenv("AZURE_OPENAI_ENDPOINT");
    final static String AZURE_OPENAI_API_KEY = System.getenv("AZURE_OPENAI_API_KEY");
    final static String CURRENT_DIRECTORY = System.getProperty("user.dir");
    
    
    public static void main(String[] args) throws IOException {

        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(new KeyCredential(AZURE_OPENAI_API_KEY))
            .endpoint(AZURE_OPENAI_ENDPOINT)
            .buildAsyncClient();

        ChatCompletion<ChatHistory> gpt35Turbo = ChatCompletion.builder()
                .withOpenAIClient(client)
                .withModelId(GPT_35_DEPLOYMENT_NAME)
                .build();

        ChatCompletion<ChatHistory> gpt4 = ChatCompletion.builder()
                .withOpenAIClient(client)
                .withModelId(GPT_4_DEPLOYMENT_NAME)
                .build();

        Kernel kernel = SKBuilders.kernel()
                .withDefaultAIService(gpt35Turbo)
                .withDefaultAIService(gpt4)
                .withPromptTemplateEngine(new HandlebarsPromptTemplateEngine())
                .build();

        // Initialize the required functions and services for the kernel
        SemanticFunction chatFunction = SemanticFunction.fromYaml("Plugins/ChatPlugin/SimpleChat.prompt.yaml");

        ChatHistory chatHistory = gpt35Turbo.createNewChat();

        BufferedReader bf = new BufferedReader(new InputStreamReader(System.in));
        while (true) {
            System.out.print("\nUser > ");
            String input = bf.readLine();
            chatHistory.addUserMessage(input);

            KernelResult result = kernel.runAsync(
                    true,
                    ContextVariables.builder().withVariable("messages", chatHistory).build(),
                    chatFunction
            ).block();

            System.out.print("Assistant > ");
            result.functionResults().forEach(
                    functionResult -> {
                        functionResult.<String>getStreamingValueAsync().subscribe(
                                message -> System.out.print(message)
                        );

                        String message = functionResult.<String>getValue();
                        chatHistory.addAssistantMessage(message);
                    }
            );
        }
    }
}