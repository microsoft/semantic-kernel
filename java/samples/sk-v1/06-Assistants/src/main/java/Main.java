
import java.util.List;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.KernelResult;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.nativefunction.NativeFunction;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.plugin.Plugin;
import com.microsoft.semantickernel.assistants.AssistantKernel;
import com.microsoft.semantickernel.assistants.AssistantThread;

import plugins.mathplugin.Math;
import plugins.searchplugin.Search;

public class Main {

    final static String GPT_35_TURBO_DEPLOYMENT_NAME = System.getenv("GPT_35_TURBO_DEPLOYMENT_NAME");
    final static String GPT_4_DEPLOYMENT_NAME = System.getenv("GPT_4_DEPLOYMENT_NAME");
    final static String AZURE_OPENAI_ENDPOINT = System.getenv("AZURE_OPENAI_ENDPOINT");
    final static String AZURE_OPENAI_API_KEY = System.getenv("AZURE_OPENAI_API_KEY");
    final static String BING_API_KEY = System.getenv("BING_API_KEY");
    final static String CURRENT_DIRECTORY = System.getProperty("user.dir");


    public static void main(String[] args) throws ConfigurationException {

        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(new KeyCredential(AZURE_OPENAI_API_KEY))
            .endpoint(AZURE_OPENAI_ENDPOINT)
            .buildAsyncClient();

        ChatCompletion<ChatHistory> gpt4Turbo = ChatCompletion.builder()
                .withOpenAIClient(client)
                .withModelId(GPT_4_DEPLOYMENT_NAME)
                .build();

        // Create the math plugin
        List<SKFunction> mathFunctions = NativeFunction.getFunctionsFromObject(new Math());
        Plugin mathPlugin = new com.microsoft.semantickernel.plugin.Plugin(
            "Math",
            mathFunctions
        );

        // Create the search plugin
        Plugin searchPlugin = new com.microsoft.semantickernel.plugin.Plugin(
            "Search",
            NativeFunction.getFunctionsFromObject(new Search(BING_API_KEY))
        );

        AssistantKernel researcher = AssistantKernel.FromConfiguration(
            CURRENT_DIRECTORY + "/Assistants/Researcher.agent.yaml",
            List.of(gpt4Turbo),
            List.of(searchPlugin),
						null
        );

        AssistantKernel mathematician = AssistantKernel.FromConfiguration(
            CURRENT_DIRECTORY + "/Assistants/Mathematician.agent.yaml",
            List.of(gpt4Turbo),
            List.of(mathPlugin),
						null
        );

        AssistantKernel designer = AssistantKernel.FromConfiguration(
            CURRENT_DIRECTORY + "/Assistants/Designer.agent.yaml",
            List.of(gpt4Turbo),
            null,
            null
        );

        AssistantKernel projectManager = AssistantKernel.FromConfiguration(
            CURRENT_DIRECTORY + "/Assistants/ProjectManager.agent.yaml",
            List.of(gpt4Turbo),
            List.of(researcher, mathematician, designer),
            null
        );

        AssistantThread thread = projectManager.createThreadAsync().block();

        while(true)
        {
            String input = System.console().readLine("User > ");
            thread.addUserMessageAsync(input);

            KernelResult result = projectManager.runAsync(thread).block();

            result.functionResults().forEach(
                functionResult -> {
                    // TODO: List<ModelMessage> messages = functionResult.getValue();
                    //  messages.forEach(
                    //    message -> {
                    //        System.console().printf("Assistant > %s%n", message);
                    //      }
                    //      );
                    String message = (String)functionResult.getValue();
                    System.console().printf("Assistant > %s%n", message);
                }
            );
        }
    }
}
