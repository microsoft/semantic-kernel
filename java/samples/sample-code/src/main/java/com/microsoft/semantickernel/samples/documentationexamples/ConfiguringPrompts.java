// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.documentationexamples;

import java.util.HashMap;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.semanticfunctions.InputVariable;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;

public class ConfiguringPrompts {

    // CLIENT_KEY is for an OpenAI client
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // AZURE_CLIENT_KEY and CLIENT_ENDPOINT are for an Azure client
    // CLIENT_ENDPOINT required if AZURE_CLIENT_KEY is set
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    private static final String CHAT_MODEL_ID = System.getenv()
        .getOrDefault("CHAT_MODEL_ID", "gpt-3.5-turbo");

    public static void main(String[] args) {
        System.out.println("======== Configuring Prompts ========");

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

        // <CreateChatCompletionService>
        ChatCompletionService chatCompletionService = ChatCompletionService.builder()
            .withModelId(CHAT_MODEL_ID)
            .withOpenAIAsyncClient(client)
            .build();
        // </CreateChatCompletionService>

        // <CreateKernel>
        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, chatCompletionService)
            .build();
        // </CreateKernel>

        // <CreateFromPrompt>
        KernelFunction<String> chat = KernelFunction.<String>createFromPrompt(
            PromptTemplateConfig.builder()
                .withName("Chat")
                .withTemplate(
                    """
                        {{ConversationSummaryPlugin.SummarizeConversation $history}}
                        User: {{$request}}
                        Assistant:
                        """.stripIndent())
                .addInputVariable(InputVariable.build(
                    "history",
                    String.class,
                    "The history of the conversation.",
                    null,
                    false))
                .addInputVariable(InputVariable.build(
                    "request",
                    String.class,
                    "The user's request.",
                    null,
                    true))
                .withExecutionSettings(new HashMap<String, PromptExecutionSettings>() {
                    {
                        put("gpt-3.5-turbo", PromptExecutionSettings.builder()
                            .withMaxTokens(1_000)
                            .withTemperature(0d)
                            .build());
                        put("gpt-4", PromptExecutionSettings.builder()
                            .withModelId("gpt-4-1106-preview")
                            .withMaxTokens(8_000)
                            .withTemperature(0.3d)
                            .build());
                    }
                })
                .build())
            .build();
        // </CreateFromPrompt>
    }
}
