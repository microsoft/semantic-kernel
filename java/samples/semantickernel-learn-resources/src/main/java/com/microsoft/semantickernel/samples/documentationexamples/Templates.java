// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.ConversationSummaryPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import java.io.InputStream;
import java.util.Arrays;
import java.util.List;
import java.util.Scanner;
import java.util.stream.Collectors;

public class Templates {

    public static InputStream INPUT = System.in;

    // CLIENT_KEY is for an OpenAI client
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // AZURE_CLIENT_KEY and CLIENT_ENDPOINT are for an Azure client
    // CLIENT_ENDPOINT required if AZURE_CLIENT_KEY is set
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-3.5-turbo");

    public static void main(String[] args) {
        System.out.println("======== Templates ========");

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null && CLIENT_ENDPOINT != null) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();
        } else if (CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        } else {
            System.out.println("No client key found");
            return;
        }

        // Customise the type converters toPromptString for ChatHistory to serialize the messages as "author: content"
        ContextVariableTypeConverter<ChatHistory> chatHistoryType = ContextVariableTypeConverter
            .builder(ChatHistory.class)
            .proxyGlobalType()
            .toPromptString(history -> {
                return history.getMessages()
                    .stream()
                    .map(message -> String.format("%s: %s",
                        message.getAuthorRole(),
                        message.getContent()))
                    .collect(Collectors.joining("\n"));
            })
            .build();

        ChatCompletionService chatCompletionService = ChatCompletionService.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        KernelPlugin plugin = KernelPluginFactory.createFromObject(
            new ConversationSummaryPlugin(), "ConversationSummaryPlugin");

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withPlugin(plugin)
            .build();

        // <create_chat>
        KernelFunction<String> chat = KernelFunctionFromPrompt.<String>createFromPrompt("""
            {{$history}}
            user: {{$request}}
            assistant:""")
            .build();
        // </create_chat>

        // <handlebars_add_variables_1>
        List<String> choices = Arrays.asList("ContinueConversation", "EndConversation");

        // Create few-shot examples
        List<ChatHistory> fewShotExamples = Arrays.asList(

            new ChatHistory() {
                {
                    addMessage(AuthorRole.USER,
                        "Can you send a very quick approval to the marketing team?");
                    addMessage(AuthorRole.SYSTEM, "Intent:");
                    addMessage(AuthorRole.ASSISTANT, "ContinueConversation");
                }
            },
            new ChatHistory() {
                {
                    addMessage(AuthorRole.USER, "Thanks, I'm done for now");
                    addMessage(AuthorRole.SYSTEM, "Intent:");
                    addMessage(AuthorRole.ASSISTANT, "EndConversation");
                }
            });
        // </handlebars_add_variables_1>

        // <handlebars_prompt>
        // Create handlebars template for intent
        KernelFunction<String> getIntent = KernelFunction.<String>createFromPrompt(
            """
                <message role="system">Instructions: What is the intent of this request?
                Do not explain the reasoning, just reply back with the intent. If you are unsure, reply with {{choices.[0]}}.
                Choices: {{choices}}.</message>

                {{#each fewShotExamples}}
                    {{#each this}}
                        <message role="{{role}}">{{content}}</message>
                    {{/each}}
                {{/each}}

                {{#each chatHistory}}
                    <message role="{{role}}">{{content}}</message>
                {{/each}}

                <message role="user">{{request}}</message>
                <message role="system">Intent:</message>
                """)
            .withTemplateFormat("handlebars")
            .build();
        // </handlebars_prompt>

        Scanner scanner = new Scanner(INPUT);
        // <use_chat>
        // Create chat history
        ChatHistory history = new ChatHistory();

        // Start the chat loop
        while (true) {
            // <handlebars_add_variables_2>
            // Get user input
            System.out.print("User > ");
            String request = scanner.nextLine();

            KernelFunctionArguments arguments = KernelFunctionArguments.builder()
                .withVariable("request", request)
                .withVariable("choices", choices)
                .withVariable("chatHistory", history)
                .withVariable("fewShotExamples", fewShotExamples)
                .build();
            // </handlebars_add_variables_2>

            // <handlebars_invoke>
            // Invoke handlebars prompt
            FunctionResult<String> intent = kernel.invokeAsync(getIntent)
                .withArguments(arguments)
                .withToolCallBehavior(
                    ToolCallBehavior.allowOnlyKernelFunctions(true,
                        plugin.get("SummarizeConversation")))
                .block();
            // </handlebars_invoke>

            // End the chat if the intent is "Stop"
            if ("EndConversation".equals(intent.getResult())) {
                break;
            }

            // Get chat response
            FunctionResult<String> chatResult = chat.invokeAsync(kernel)
                .withArguments(
                    KernelFunctionArguments.builder()
                        .withVariable("request", request)
                        .withVariable("history", history, chatHistoryType)
                        .build())
                .block();

            String message = chatResult.getResult();
            System.out.printf("Assistant > %s\n", message);

            // Append to history
            history.addUserMessage(request);
            history.addAssistantMessage(message);
        }
        // </use_chat>
    }

}
