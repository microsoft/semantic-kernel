package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.plugin.KernelFunctionFactory;

public class Example27_PromptFunctionsUsingChatGPT {


    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) {

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
        System.out.println("======== Using Chat GPT model for text generation ========");

        ChatCompletionService openAIChatCompletion = ChatCompletionService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion)
            .build();

        var func = KernelFunctionFactory.<String>createFromPrompt(
            "List the two planets closest to '{{$input}}', excluding moons, using bullet points.");

        var result = func.invokeAsync(
                kernel,
                KernelFunctionArguments.builder()
                    .withVariable("input", "Jupiter")
                    .build(),
                ContextVariableTypes.getGlobalVariableTypeForClass(String.class)
            )
            .block();
        System.out.println(result.getResult());

    }
}
