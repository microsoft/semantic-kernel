import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionYaml;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Path;

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

        // Initialize the required functions and services for the kernel
        KernelFunction chatFunction = KernelFunctionYaml.fromYaml(
            Path.of("Plugins/ChatPlugin/PersonaChat.prompt.yaml"));

        ChatCompletionService gpt35Turbo = ChatCompletionService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(GPT_35_DEPLOYMENT_NAME != null ? GPT_35_DEPLOYMENT_NAME : "gpt-35-turbo")
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, gpt35Turbo)
            .withPromptTemplate(new HandlebarsPromptTemplate())
            .build();

        ChatHistory chatHistory = new ChatHistory();

        BufferedReader bf = new BufferedReader(new InputStreamReader(System.in));
        while (true) {
            System.out.print("\nUser > ");
            String input = bf.readLine();
            chatHistory.addUserMessage(input);

            // Run the chat function
            // The persona chat function uses the persona variable to set the persona of the chat using a system message
            // See Plugins/ChatPlugin/PersonaChat.prompt.yaml for the full prompt
            FunctionResult<String> message = kernel
                .invokeAsync(
                    chatFunction,
                    KernelArguments
                        .builder()
                        .withVariable("messages", chatHistory)
                        .withVariable("persona",
                            "You are a snarky (yet helpful) teenage assistant. Make sure to use hip slang in every response.")
                        .build(),
                    String.class
                )
                .block();

            System.out.print("Assistant > ");
            System.out.print(message.getResult());
            chatHistory.addAssistantMessage(message.getResult());
        }
    }
}
