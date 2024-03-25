package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.ConversationSummaryPlugin;
import com.microsoft.semantickernel.semanticfunctions.HandlebarsPromptTemplateFactory;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionYaml;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;
import java.util.Scanner;

public class SerializingPrompts {
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv().getOrDefault("MODEL_ID", "gpt-35-turbo-2");

    private static final String PLUGINS_DIR = "java/samples/sample-code/src/main/resources/Plugins";

    public static void main(String[] args) throws IOException {
        System.out.println("======== Serializing Prompts ========");
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

        // Create few-shot examples
        ChatHistory continueConversation = new ChatHistory(false);
        continueConversation.addMessage(AuthorRole.USER, "Can you send a very quick approval to the marketing team?");
        continueConversation.addMessage(AuthorRole.SYSTEM, "Intent:");
        continueConversation.addMessage(AuthorRole.ASSISTANT, "ContinueConversation");
        ChatHistory endConversation = new ChatHistory(false);
        endConversation.addMessage(AuthorRole.USER, "Can you send the full update to the marketing team?");
        endConversation.addMessage(AuthorRole.SYSTEM, "Intent:");
        endConversation.addMessage(AuthorRole.ASSISTANT, "EndConversation");

        List<ChatHistory> fewShotExamples = List.of(continueConversation, endConversation);

        // <InvokeSerializedPrompts>
        // Create Kernel
        Kernel kernel = Kernel.builder()
                .withAIService(ChatCompletionService.class, ChatCompletionService.builder()
                        .withModelId(MODEL_ID)
                        .withOpenAIAsyncClient(client)
                        .build())
                .withPlugin(KernelPluginFactory.createFromObject(new ConversationSummaryPlugin(), "ConversationSummaryPlugin"))
                .build();

        // Load prompts
        var prompts = KernelPluginFactory.importPluginFromDirectory(
                Path.of(PLUGINS_DIR), "Prompts", null);

        // Load prompt from YAML
        // <LoadPromptFromYAML>
        var getIntent = KernelFunctionYaml.fromPromptYaml(
                Files.readString(Path.of(PLUGINS_DIR, "Prompts", "getIntent.prompt.yaml")),
                new HandlebarsPromptTemplateFactory());
        // </LoadPromptFromYAML>

        // Create choices
        List<String> choices = Arrays.asList("ContinueConversation", "EndConversation");

        // Create chat history
        ChatHistory history = new ChatHistory();

        // Start the chat loop
        Scanner scanner = new Scanner(System.in);
        System.out.print("User > ");
        String userInput;
        while (!(userInput = scanner.nextLine()).isEmpty()) {
            // Invoke handlebars prompt

            // <InvokePromptFromYaml>
            var intent = kernel.invokeAsync(getIntent)
                    .withArguments(KernelFunctionArguments.builder()
                            .withVariable("request", userInput)
                            .withVariable("choices", choices)
                            .withVariable("history", history)
                            .withVariable("fewShotExamples", fewShotExamples)
                            .build())
                    .block();
            // </InvokePromptFromYaml>

            // End the chat if the intent is "Stop"
            if (intent.getResult().equals("EndConversation")) {
                break;
            }

            var reply = kernel.invokeAsync(prompts.get("Chat"))
                    .withArguments(KernelFunctionArguments.builder()
                            .withVariable("request", userInput)
                            .withVariable("history",
                                    String.join("\n", history.getMessages().stream().map(m -> m.getAuthorRole() + " > " + m.getContent()).toList()))
                            .build())
                    .withResultType(String.class)
                    .block().getResult();

            System.out.println("Assistant" + " > " + reply);

            // Append to history
            history.addUserMessage(userInput);
            history.addAssistantMessage(reply);

            // Get user input again
            System.out.print("User > ");
        }
        // </InvokeSerializedPrompts>
    }
}