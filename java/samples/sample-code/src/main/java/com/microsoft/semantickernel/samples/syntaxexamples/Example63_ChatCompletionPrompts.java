package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import java.util.concurrent.CountDownLatch;

public class Example63_ChatCompletionPrompts {

    private static final String CLIENT_KEY = System.getenv("CLIENT_KEY");
    private static final String AZURE_CLIENT_KEY = System.getenv("AZURE_CLIENT_KEY");

    // Only required if AZURE_CLIENT_KEY is set
    private static final String CLIENT_ENDPOINT = System.getenv("CLIENT_ENDPOINT");
    private static final String MODEL_ID = System.getenv()
        .getOrDefault("MODEL_ID", "gpt-35-turbo");

    public static void main(String[] args) throws InterruptedException {

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

        ChatCompletionService openAIChatCompletion = ChatCompletionService.builder()
            .withOpenAIAsyncClient(client)
            .withModelId(MODEL_ID)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(ChatCompletionService.class, openAIChatCompletion)
            .build();

        String chatPrompt = """
            <message role="user">What is Seattle?</message>
            <message role="system">Respond with JSON.</message>
            """.stripIndent();

        var chatSemanticFunction = KernelFunctionFromPrompt.create(chatPrompt);
        var chatPromptResult = kernel.invokeAsync(chatSemanticFunction).block();

        System.out.println("Chat Prompt:");
        System.out.println(chatPrompt);
        System.out.println("Chat Prompt Result:");
        System.out.println(chatPromptResult.getResult());

        CountDownLatch cdl = new CountDownLatch(1);
        System.out.println("Chat Prompt Result:");
        kernel
            .invokeAsync(chatSemanticFunction)
            .doFinally(x -> cdl.countDown())
            .subscribe(result -> System.out.println(result.getResult()));

        cdl.await();
    }
}
