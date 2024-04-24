// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.azure.identity.InteractiveBrowserCredential;
import com.azure.identity.InteractiveBrowserCredentialBuilder;
import com.microsoft.graph.serviceclient.GraphServiceClient;
import com.microsoft.semantickernel.aiservices.openai.chatcompletion.OpenAIChatCompletion;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;

import java.util.Scanner;

public class BookingAgent {

    // Config for OpenAI
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo-2");

    // Config for Graph
    // https://learn.microsoft.com/en-us/graph/tutorials/java?tabs=aad&tutorial-step=1
    private static final String TENANT_ID = System.getenv("TENANT_ID");
    private static final String CLIENT_ID = System.getenv("CLIENT_ID");
    // Booking Business ID
    private static final String BOOKING_BUSINESS_ID = System.getenv("BOOKING_BUSINESS_ID");
    // Service ID for the booking business
    private static final String SERVICE_ID = System.getenv("SERVICE_ID");
    // Must match the redirect URL in the Azure AD app registration
    private static final String REDIRECT_URL = System.getenv("REDIRECT_URL");
    private static GraphServiceClient userClient;

    public static void initializeGraph() {
        InteractiveBrowserCredential interactiveBrowserCredential = new InteractiveBrowserCredentialBuilder()
            .clientId(CLIENT_ID)
            .tenantId(TENANT_ID)
            .redirectUrl(REDIRECT_URL)
            .build();

        userClient = new GraphServiceClient(interactiveBrowserCredential,
            "User.Read", "BookingsAppointment.ReadWrite.All");
    }

    public static void main(String[] args) throws NoSuchMethodException {
        System.out.println("======== Open AI - Booking System ========");

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

        initializeGraph();

        KernelPlugin plugin = KernelPluginFactory.createFromObject(new BookingPlugin(
            userClient,
            BOOKING_BUSINESS_ID,
            SERVICE_ID,
            "UTC"), "BookingRestaurant");

        ChatCompletionService chat = OpenAIChatCompletion.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        Kernel kernel = Kernel.builder()
            .withPlugin(plugin)
            .withAIService(ChatCompletionService.class, chat)
            .build();

        ChatHistory chatHistory = new ChatHistory();

        Scanner scanner = new Scanner(System.in);
        String userMessage;
        System.out.println("User > ");

        while ((userMessage = scanner.nextLine()) != null) {

            chatHistory.addUserMessage(userMessage);
            InvocationContext invocationContext = InvocationContext.builder()
                .withToolCallBehavior(ToolCallBehavior.allowAllKernelFunctions(true)).build();

            ChatMessageContent<?> result = chat
                .getChatMessageContentsAsync(chatHistory, kernel, invocationContext).block().get(0);
            chatHistory.addAssistantMessage(result.getContent());

            System.out.println("Assistant > " + result);
            System.out.println("User > ");
        }
    }
}
