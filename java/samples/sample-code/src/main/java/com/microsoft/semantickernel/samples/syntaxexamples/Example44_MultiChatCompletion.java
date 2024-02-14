package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;

public class Example44_MultiChatCompletion {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) {
        System.out.println("======== Open AI - Multiple Chat Completion ========");

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

        ChatCompletionService chatGPT = OpenAIChatCompletion.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        System.out.println("Chat content:");
        System.out.println("------------------------");

        ChatHistory chatHistory = new ChatHistory("You are a librarian, expert about books");
        var executionSettings = PromptExecutionSettings.builder()
            .withMaxTokens(1024)
            .withTemperature(1)
            .withResultsPerPrompt(2)
            .build();

        chatHistory.addUserMessage("Hi, I'm looking for 3 different book suggestions about sci-fi");
        messageOutput(chatHistory);

        GPTReply(chatGPT, chatHistory, executionSettings);
    }

    private static void messageOutput(ChatHistory chatHistory) {
        var message = chatHistory.getLastMessage().get();
        System.out.println(message.getAuthorRole() + ": " + message.getContent());
        System.out.println("------------------------");
    }

    private static void GPTReply(ChatCompletionService chatGPT, ChatHistory chatHistory,
        PromptExecutionSettings settings) {

        var invocationContext = InvocationContext.builder().withPromptExecutionSettings(settings)
            .build();

        var reply = chatGPT.getChatMessageContentsAsync(chatHistory, null, invocationContext)
            .block();

        reply.forEach(chatMessageContent -> {
            chatHistory.addAssistantMessage(chatMessageContent.getContent());
            messageOutput(chatHistory);
        });
    }
}
