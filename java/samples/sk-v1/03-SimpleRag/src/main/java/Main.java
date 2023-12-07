
import java.io.IOException;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.KernelResult;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.nativefunction.NativeFunction;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.plugin.Plugin;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunction;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplateEngine;
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
        SKFunction chatFunction = SemanticFunction.fromYaml("Plugins/ChatPlugin/GroundedChat.prompt.yaml");

        ChatCompletion<ChatHistory> gpt35Turbo = ChatCompletion.builder()
            .withOpenAIClient(client)
            .withModelId(GPT_35_DEPLOYMENT_NAME)
            .build();

        ChatCompletion<ChatHistory> gpt4 = ChatCompletion.builder()
                .withOpenAIClient(client)
                .withModelId(GPT_4_DEPLOYMENT_NAME)
                .build();

        // Create the search plugin
        Plugin searchPlugin = new com.microsoft.semantickernel.plugin.Plugin(
            "Search",
            NativeFunction.getFunctionsFromObject(new Search(BING_API_KEY))
        );                

        Kernel kernel = SKBuilders.kernel()
            .withDefaultAIService(gpt35Turbo)
            .withDefaultAIService(gpt4)
            .withPromptTemplateEngine(new HandlebarsPromptTemplateEngine())
            .withPlugins(searchPlugin)
            .build();

        ChatHistory chatHistory = gpt35Turbo.createNewChat();
        while(true)
        {
            String input = System.console().readLine("User > ");
            chatHistory.addUserMessage(input);

            // Run the chat function
            // The grounded chat function uses the search plugin to perform a Bing search to ground the response
            // See Plugins/ChatPlugin/GroundedChat.prompt.yaml for the full prompt
            KernelResult result = kernel.runAsync(
                true, // streaming
                ContextVariables.builder()
                    .withVariable("messages", chatHistory)
                    .withVariable("persona", "You are a snarky (yet helpful) teenage assistant. Make sure to use hip slang in every response.")
                .build(),
                chatFunction
            ).block();

            System.console().printf("Assistant > ");
            result.functionResults().forEach(
                functionResult -> {
                    functionResult.<String>getStreamingValueAsync().subscribe(
                        message -> System.console().printf(message)
                    ); 
                    String message = functionResult.<String>getValueAsync().block();
                    chatHistory.addAssistantMessage(message);
                }
            );
        }            
    }
}
