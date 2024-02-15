package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.TimePlugin;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateFactory;
import com.microsoft.semantickernel.services.ServiceNotFoundException;
import com.microsoft.semantickernel.implementation.EmbeddedResourceLoader;

import java.io.FileNotFoundException;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;

public class Example30_ChatWithPrompts {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) throws FileNotFoundException, ServiceNotFoundException {
        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();

        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        ChatCompletionService openAIChatCompletion = ChatCompletionService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion)
            .build();

        System.out.println("======== Chat with prompts ========");

        /*
         * Load 3 files:
         * - 30-system-prompt.txt: the system prompt, used to initialize the chat session.
         * - 30-user-context.txt: the user context, e.g. a piece of a document the user selected and
         * is asking to process.
         * - 30-user-prompt.txt: the user prompt, just for demo purpose showing that one can
         * leverage the same approach also to augment user messages.
         */

        var systemPromptTemplate = EmbeddedResourceLoader.readFile("30-system-prompt.txt",
            Example30_ChatWithPrompts.class);
        var selectedText = EmbeddedResourceLoader.readFile("30-user-context.txt",
            Example30_ChatWithPrompts.class);
        var userPromptTemplate = EmbeddedResourceLoader.readFile("30-user-prompt.txt",
            Example30_ChatWithPrompts.class);

        // As an example, we import the time plugin, which is used in system prompt to read the current date.
        // We could also use a variable, this is just to show that the prompt can invoke functions.
        KernelPlugin timePlugin = KernelPluginFactory.createFromObject(
            new TimePlugin(), "time");
        kernel.addPlugin(timePlugin);

        // Adding required arguments referenced by the prompt templates.

        var arguments = KernelFunctionArguments
            .builder()
            .withVariable("selectedText", selectedText)
            .withVariable("startTime", DateTimeFormatter.ofPattern("hh:mm:ss a zz").format(
                ZonedDateTime.of(2000, 1, 1, 1, 1, 1, 1, ZoneId.systemDefault())))
            .withVariable("userMessage", "extract locations as a bullet point list")
            .build();

        // Render the system prompt. This string is used to configure the chat.
        // This contains the context, ie a piece of a wikipedia page selected by the user.
        String systemMessage = PromptTemplateFactory
            .build(new PromptTemplateConfig(systemPromptTemplate))
            .renderAsync(kernel, arguments, null)
            .block();

        System.out.println("------------------------------------\n" + systemMessage);

        // Render the user prompt. This string is the query sent by the user
        // This contains the user request, ie "extract locations as a bullet point list"
        String userMessage = PromptTemplateFactory
            .build(new PromptTemplateConfig(userPromptTemplate))
            .renderAsync(kernel, arguments, null)
            .block();

        System.out.println("------------------------------------\n" + userMessage);

        // Client used to request answers
        var chatCompletion = kernel.getService(ChatCompletionService.class);

        // The full chat history. Depending on your scenario, you can pass the full chat if useful,
        // or create a new one every time, assuming that the "system message" contains all the
        // information needed.
        var chatHistory = new ChatHistory(systemMessage);

        // Add the user query to the chat history
        chatHistory.addUserMessage(userMessage);

        // Finally, get the response from AI
        var answer = chatCompletion
            .getChatMessageContentsAsync(chatHistory, kernel, null)
            .block();
        System.out.println(
            "------------------------------------\n" + answer.stream().findFirst().get()
                .getContent());
    }
}
