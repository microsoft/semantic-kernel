
import java.io.IOException;
import java.util.List;

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

import plugins.mathplugin.Math;

public class Main {
    
    final static String GPT_35_TURBO_DEPLOYMENT_NAME = System.getenv("GPT_35_TURBO_DEPLOYMENT_NAME");
    final static String GPT_4_DEPLOYMENT_NAME = System.getenv("GPT_4_DEPLOYMENT_NAME");
    final static String AZURE_OPENAI_ENDPOINT = System.getenv("AZURE_OPENAI_ENDPOINT");
    final static String AZURE_OPENAI_API_KEY = System.getenv("AZURE_OPENAI_API_KEY");
    final static String CURRENT_DIRECTORY = System.getProperty("user.dir");
    
    
    public static void main(String[] args) throws ConfigurationException, IOException {

        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(new KeyCredential(AZURE_OPENAI_API_KEY))
            .endpoint(AZURE_OPENAI_ENDPOINT)
            .buildAsyncClient();


        // Initialize the required functions and services for the kernel
        SKFunction chatFunction = SemanticFunction.fromYaml("/Plugins/ChatPlugin/Chat.prompt.yaml");

        ChatCompletion<ChatHistory> gpt35Turbo = ChatCompletion.builder()
            .withOpenAIClient(client)
            .withModelId(GPT_35_TURBO_DEPLOYMENT_NAME)
            .build();

        ChatCompletion<ChatHistory> gpt4 = ChatCompletion.builder()
                .withOpenAIClient(client)
                .withModelId(GPT_4_DEPLOYMENT_NAME)
                .build();

        // Create the intent plugin
        Plugin intentPlugin = new com.microsoft.semantickernel.plugin.Plugin(
            "Intent",
            SemanticFunction.fromYaml("/Plugins/IntentPlugin/GetNextStep.prompt.yaml")
        );  
        
        // Create the math plugin
        List<SKFunction> mathFunctions = NativeFunction.getFunctionsFromObject(new Math());
        mathFunctions.add(SemanticFunction.fromYaml("/Plugins/MathPlugin/GenerateMathProblem.prompt.yaml"));
        Plugin math = new com.microsoft.semantickernel.plugin.Plugin(
            "Math",
            mathFunctions
        );

        Kernel kernel = SKBuilders.kernel()
            .withDefaultAIService(gpt35Turbo)
            .withDefaultAIService(gpt4)
            .withPromptTemplateEngine(new HandlebarsPromptTemplateEngine())
            .withPlugins(intentPlugin, math)
            .build();

        ChatHistory chatHistory = gpt35Turbo.createNewChat();
        while(true)
        {
            String input = System.console().readLine("User > ");
            chatHistory.addUserMessage(input);

            // Run the chat function
            // The dynamic chat function uses a planner to create a plan that solves a math problem
            // See Plugins/MathPlugin/Math.cs for the code that runs the planner
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
