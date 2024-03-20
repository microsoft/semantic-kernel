package com.microsoft.semantickernel.samples.documentationexamples;

import java.util.Arrays;
import java.util.List;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.ConversationSummaryPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;

public class FunctionsWithinPrompts {
    
    // CLIENT_KEY is for an OpenAI client
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // AZURE_CLIENT_KEY and CLIENT_ENDPOINT are for an Azure client
    // CLIENT_ENDPOINT required if AZURE_CLIENT_KEY is set
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    private static final String CHAT_MODEL_ID = System.getenv()
        .getOrDefault("CHAT_MODEL_ID", "gpt-3.5-turbo");
            
    public static void main(String[] args) {
        
        System.out.println("======== Functions within Prompts ========");

        OpenAIAsyncClient client = null;
        
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

        ChatCompletionService chatCompletionService = ChatCompletionService.builder()
            .withModelId(CHAT_MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withPlugin(KernelPluginFactory.createFromObject(new ConversationSummaryPlugin(), "ConversationSummaryPlugin"))
            .build();

        List<String> choices = Arrays.asList("ContinueConversation", "EndConversation");

        // Create few-shot examples
        List<ChatHistory> fewShotExamples = Arrays.asList(

            new ChatHistory() 
            {{
                addMessage(AuthorRole.USER, "Can you send a very quick approval to the marketing team?");
                addMessage(AuthorRole.SYSTEM, "Intent:");
                addMessage(AuthorRole.ASSISTANT, "ContinueConversation");
            }},
            new ChatHistory()
            {{
                addMessage(AuthorRole.USER, "Can you send the full update to the marketing team?");
                addMessage(AuthorRole.SYSTEM, "Intent:");
                addMessage(AuthorRole.ASSISTANT, "EndConversation");
            }}
        );

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

                {{ConversationSummaryPlugin-SummarizeConversation history}}

                <message role="user">{{request}}</message>
                <message role="system">Intent:</message>
                """
            )
            .withTemplateFormat("handlebars")
            .build();

        // Create a Semantic Kernel template for chat
        KernelFunction<String> chat = KernelFunction.<String>createFromPrompt(
            """
            {{ConversationSummaryPlugin.SummarizeConversation $history}}
            User: {{$request}}
            Assistant: 
            """
        )
        .build();

        // Create chat history
        ChatHistory history = new ChatHistory();

        // Start the chat loop
        while (true)
        {
            // Get user input
            System.console().printf("User > ");
            String request = System.console().readLine();

            // Invoke handlebars prompt
            FunctionResult<String> intent = getIntent.invokeAsync(
                kernel,
                KernelFunctionArguments.builder()
                    .withVariable("request", request)
                    .withVariable("choices", choices)
                    .withVariable("history", history)
                    .withVariable("fewShotExamples", fewShotExamples)
                    .build(),
                null,
                null
            )
            .block();

            // End the chat if the intent is "Stop"
            if ("EndConversation".equals(intent.getResult()))
            {
                break;
            }

            // Get chat response
            FunctionResult<String> chatResult = chat.invokeAsync(
                kernel,
                KernelFunctionArguments.builder()
                    .withVariable("request", request)
                    .withVariable("history", history)
                    .build(),
                    null,
                    null
            ).block();

            // Stream the response
            String message = chatResult.getResult();
            System.console().printf("Assistant > %s\n", message);

            // Append to history
            history.addUserMessage(request);
            history.addAssistantMessage(message);
        }
    }

}
