package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.services.AIServiceSelection;
import com.microsoft.semantickernel.services.BaseAIServiceSelector;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.util.Map;
import javax.annotation.Nullable;

public class Example62_CustomAIServiceSelector {


    private static final boolean USE_AZURE_CLIENT = Boolean.parseBoolean(
        System.getenv("USE_AZURE_CLIENT"));
    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");

    // Only required if USE_AZURE_CLIENT is true
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");

    public static void main(String[] args) {
        System.out.println("======== Example62_CustomAIServiceSelector ========");

        OpenAIAsyncClient client;

        if (USE_AZURE_CLIENT) {
            client = new OpenAIClientBuilder()
                .credential(new AzureKeyCredential(CLIENT_KEY))
                .endpoint(CLIENT_ENDPOINT)
                .buildAsyncClient();
        } else {
            client = new OpenAIClientBuilder()
                .credential(new KeyCredential(CLIENT_KEY))
                .buildAsyncClient();
        }

        // Build a kernel with multiple chat completion services

        var openAIChatCompletion = ChatCompletionService.builder()
            .withOpenAIAsyncClient(client)
            .withServiceId("AzureOpenAIChat")
            .withModelId("gpt-35-turbo-2")
            .build();

        var textGenerationService = TextGenerationService.builder()
            .withOpenAIAsyncClient(client)
            .withServiceId("AzureOpenAIText")
            .withModelId("text-davinci-003")
            .build();

        var kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion)
            .withAIService(TextGenerationService.class, textGenerationService)
            .withServiceSelector(CustomAIServiceSelector::new)
            .build();

        var prompt = "Hello AI, what can you do for me?";

        KernelArguments arguments = KernelArguments.builder().build();

        KernelFunction func = KernelFunctionFromPrompt
            .builder()
            .withTemplate(prompt)
            .withDefaultExecutionSettings(
                PromptExecutionSettings.builder()
                    .withTopP(1.0)
                    .build()
            )
            .build();

        var result = kernel.invokeAsync(func, arguments, String.class).block();
        System.out.println(result.getResultVariable());
    }

    // A dumb AIServiceSelector that just returns the first service and execution settings it finds
    static class CustomAIServiceSelector extends BaseAIServiceSelector {

        public CustomAIServiceSelector(Map<Class<? extends AIService>, AIService> services) {
            super(services);
        }

        @Nullable
        @Override
        public <T extends AIService> AIServiceSelection<T> trySelectAIService(
            Class<T> serviceType,

            @Nullable
            KernelFunction function,

            @Nullable
            KernelArguments arguments,
            Map<Class<? extends AIService>, AIService> services) {

            // Just get the first one
            PromptExecutionSettings executionSettings = function.getExecutionSettings()
                .values().stream().findFirst().get();
            AIService service = services.values().stream().findFirst().get();

            return new AIServiceSelection(
                service,
                executionSettings
            );
        }
    }
}
