import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.AzureOpenAIChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionYaml;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import plugins.searchplugin.Search;

public class Main {

    final static String GPT_35_DEPLOYMENT_NAME = System.getenv("GPT_35_DEPLOYMENT_NAME");
    final static String GPT_4_DEPLOYMENT_NAME = System.getenv("GPT_4_DEPLOYMENT_NAME");
    final static String AZURE_OPENAI_ENDPOINT = System.getenv("AZURE_OPENAI_ENDPOINT");
    final static String AZURE_OPENAI_API_KEY = System.getenv("AZURE_OPENAI_API_KEY");
    final static String BING_API_KEY = System.getenv("BING_API_KEY");
    final static String CURRENT_DIRECTORY = System.getProperty("user.dir");


    public static void main(String[] args) throws IOException {

        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(new KeyCredential(AZURE_OPENAI_API_KEY))
            .endpoint(AZURE_OPENAI_ENDPOINT)
            .buildAsyncClient();

        // Initialize the required functions and services for the kernel
        KernelFunction chatFunction = KernelFunctionYaml.fromYaml(
            Path.of("Plugins/ChatPlugin/GroundedChat.prompt.yaml"));

        ChatCompletionService gpt35Turbo = AzureOpenAIChatCompletion.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(GPT_35_DEPLOYMENT_NAME != null ? GPT_35_DEPLOYMENT_NAME : "gpt-35-turbo")
            .build();

        // Create the search plugin
        KernelPlugin searchPlugin = KernelPluginFactory.createFromObject(
            new Search(BING_API_KEY),
            "Search"
        );

        Kernel kernel = SKBuilders.kernel()
            .withDefaultAIService(ChatCompletionService.class, gpt35Turbo)
            .withPromptTemplateEngine(new HandlebarsPromptTemplate())
            .withPlugins(searchPlugin)
            .build();

        ChatHistory chatHistory = new ChatHistory();
        while (true) {
            String input = System.console().readLine("User > ");
            chatHistory.addUserMessage(input);

            // Run the chat function
            // The grounded chat function uses the search plugin to perform a Bing search to ground the response
            // See Plugins/ChatPlugin/GroundedChat.prompt.yaml for the full prompt
            List<String> result = kernel.invokeStreamingAsync(
                    chatFunction,
                    KernelArguments.builder()
                        .withVariable("messages", chatHistory)
                        .withVariable("persona",
                            "You are a snarky (yet helpful) teenage assistant. Make sure to use hip slang in every response.")
                        .build(),
                    String.class
                ).collectList()
                .block();

            System.console().printf("Assistant > ");
            result.forEach(
                functionResult -> {
                    System.out.println(functionResult);
                    chatHistory.addAssistantMessage(functionResult);
                }
            );
        }
    }
}
