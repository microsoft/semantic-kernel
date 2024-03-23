// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.ToolCallBehavior;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import java.io.InputStream;
import java.util.Scanner;

public class Plugin {
    // CLIENT_KEY is for an OpenAI client
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv().getOrDefault("MODEL_ID", "gpt-35-turbo-2");

    public static void main(String[] args) {
        System.out.println("======== Plugin ========");

        OpenAIAsyncClient client;

        if (AZURE_CLIENT_KEY != null && CLIENT_ENDPOINT != null) {
            // <build_client>
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(AZURE_CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();
            // </build_client>
        } else if (CLIENT_KEY != null) {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        } else {
            System.out.println("No client key found");
            return;
        }


        // <KernelCreation>
        ChatCompletionService chatCompletionService = ChatCompletionService.builder()
            .withModelId(MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();

        KernelPlugin plugin = KernelPluginFactory.createFromObject(
            new LightPlugin(), "LightPlugin");

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .withPlugin(plugin)
            .build();
        // </KernelCreation>

        // <Chat>
        // Create chat history
        var history = new ChatHistory();

        // Start the conversation
        System.out.print("User > ");
        Scanner scanner = new Scanner(System.in);
        String userInput;
        while (!(userInput = scanner.nextLine()).isEmpty()) {
            // Add user input to history
            history.addUserMessage(userInput);

            // Enable auto function calling
            var invocationContext = InvocationContext.builder()
                .withToolCallBehavior(
                    ToolCallBehavior.allowAllKernelFunctions(true))
                .build();

            // Get the response from the AI
            var result = chatCompletionService
                .getChatMessageContentsAsync(
                    history,
                    kernel,
                    invocationContext)
                .block();

            String message = result.get(result.size() - 1).getContent();
            System.out.printf("Assistant > %s%n", message);

            // Add the message from the agent to the chat history
            history.addAssistantMessage(message);
        }
        // </Chat>
    }

    // <LightPlugin>
    public static class LightPlugin {

        public boolean isOn = false;

        @DefineKernelFunction(name = "getState", description = "Gets the state of the light.'")
        String getState() {
            return isOn ? "on" : "off";
        }

        @DefineKernelFunction(name = "changeState", description = "Changes the state of the light.'")
        public String changeState(
            @KernelFunctionParameter(name = "newState",
                    description = "The new state of the light, boolean true==on, false==off.",
                    type = boolean.class) boolean newState) {

            this.isOn = newState;
            String state = getState();

            // Print the state to the console
            System.out.printf("[Light is now %s]%n", state);
            return state;
        }
    }
    // </LightPlugin>
}
