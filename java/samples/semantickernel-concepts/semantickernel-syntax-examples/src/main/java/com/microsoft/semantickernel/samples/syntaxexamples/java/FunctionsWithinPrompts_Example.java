// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples.java;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.exceptions.ConfigurationException;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.ConversationSummaryPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import java.io.IOException;
import java.io.InputStream;
import java.util.Arrays;
import java.util.List;
import java.util.Scanner;
import java.util.stream.Collectors;

public class FunctionsWithinPrompts_Example {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo-2");

    public static InputStream INPUT = System.in;

    public static void main(String[] args) throws ConfigurationException, IOException {

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

        ChatCompletionService chatCompletionService = ChatCompletionService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        KernelPlugin plugin = KernelPluginFactory.createFromObject(
            new ConversationSummaryPlugin(), "ConversationSummaryPlugin");

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withPlugin(plugin)
            .build();

        List<String> choices = Arrays.asList("ContinueConversation", "EndConversation");

        // Create few-shot examples
        List<ChatHistory> fewShotExamples = Arrays.asList(
            new ChatHistory(
                Arrays.asList(
                    new ChatMessageContent<String>(AuthorRole.USER,
                        "Can you send a very quick approval to the marketing team?"),
                    new ChatMessageContent<String>(AuthorRole.SYSTEM, "Intent:"),
                    new ChatMessageContent<String>(AuthorRole.ASSISTANT,
                        "ContinueConversation"))),

            new ChatHistory(
                Arrays.asList(
                    new ChatMessageContent<String>(AuthorRole.USER,
                        "Thats all"),
                    new ChatMessageContent<String>(AuthorRole.SYSTEM, "Intent:"),
                    new ChatMessageContent<String>(AuthorRole.ASSISTANT, "EndConversation"))));

        // Create handlebars template for intent
        // <IntentFunction>
        var getIntent = KernelFunctionFromPrompt
            .<String>createFromPrompt(
                """
                    <message role="system">Instructions: What is the intent of this request?
                    Do not explain the reasoning, just reply back with the intent. If you are unsure, reply with {{choices.[0]}}.
                    Choices: {{choices}}.</message>

                    {{#each fewShotExamples}}
                        {{#each this}}
                            <message role="{{role}}">{{content}}</message>
                        {{/each}}
                    {{/each}}

                    <message role="user">{{request}}</message>
                    <message role="system">Intent:</message>"""
                    .stripIndent())
            .withTemplateFormat("handlebars")
            .build();
        // </IntentFunction>

        // Create a Semantic Kernel template for chat
        // <FunctionFromPrompt>
        var chat = KernelFunctionFromPrompt.<String>createFromPrompt("""
            Answer the users question below taking into account the conversation so far.

            [START SUMMARY OF CONVERSATION SO FAR]
                {{ConversationSummaryPlugin.SummarizeConversation $history}}
            [END SUMMARY OF CONVERSATION SO FAR]

            User: {{$request}}
            Assistant:
            """.stripIndent()).build();
        // </FunctionFromPrompt>

        Scanner scanner = new Scanner(INPUT);

        ChatHistory history = new ChatHistory();
        // Start the chat loop
        while (true) {
            // Get user input
            System.out.println("User > ");
            var request = scanner.nextLine();

            String historyString = history.getMessages()
                .stream()
                .map(message -> message.getAuthorRole() + ": " + message.getContent())
                .collect(Collectors.joining("\n"));

            /*
             * Renders to:
             * 
             * <message role=\"system\">Instructions: What is the intent of this request?
             * Do not explain the reasoning, just reply back with the intent. If you are unsure,
             * reply with .
             * Choices: ContinueConversation,EndConversation.</message>
             * 
             * <message role=\"user\">Can you send a very quick approval to the marketing
             * team?</message>
             * <message role=\"system\">Intent:</message>
             * <message role=\"assistant\">ContinueConversation</message>
             * <message role=\"user\">Can you send the full update to the marketing team?</message>
             * <message role=\"system\">Intent:</message>
             * <message role=\"assistant\">EndConversation</message>
             * 
             * <message role=\"user\">Can you send an approval to the marketing team?</message>
             * <message role=\"system\">Intent:</message>
             */

            // Invoke handlebars prompt
            var intent = kernel.invokeAsync(getIntent)
                .withArguments(
                    KernelFunctionArguments.builder()
                        .withVariable("request", request)
                        .withVariable("choices", choices)
                        .withVariable("history", historyString)
                        .withVariable("fewShotExamples", fewShotExamples)
                        .build())
                .withToolCallBehavior(
                    ToolCallBehavior.allowOnlyKernelFunctions(true,
                        plugin.get("SummarizeConversation")))
                .block();

            // End the chat if the intent is "Stop"
            if ("EndConversation".equalsIgnoreCase(intent.getResult())) {
                break;
            }

            // Get chat response
            var chatResult = kernel.invokeAsync(chat)
                .withArguments(
                    KernelFunctionArguments.builder()
                        .withVariable("request", request)
                        .withVariable("history", historyString)
                        .build())
                .block();

            String message = chatResult.getResult();
            System.out.println("Assistant: " + message);
            System.out.println();

            // Append to history
            history.addUserMessage(request);
            history.addAssistantMessage(message);
        }
    }
}
