package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.azure.ai.openai.OpenAIClientBuilder;
import com.azure.core.credential.AzureKeyCredential;
import com.azure.core.credential.KeyCredential;
import com.azure.core.http.HttpClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.plugin.KernelPluginCollection;
import com.microsoft.semantickernel.plugin.KernelPluginFactory;
import com.microsoft.semantickernel.samples.plugins.ConversationSummaryPlugin;
import com.microsoft.semantickernel.services.OrderedAIServiceSelector;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;

public class Example42_KernelBuilder {

    public static void main(String[] args) {

        /////////////////////////////////////////////////////////
        // KernelBuilder provides a simple way to configure a Kernel. This constructs a kernel
        // with logging and an Azure OpenAI chat completion service configured.
        OpenAIAsyncClient client = new OpenAIClientBuilder()
            .credential(new AzureKeyCredential("a-key"))
            .endpoint("an-endpoint")
            .buildAsyncClient();

        Kernel kernel1 = Kernel.builder()
            .withAIService(ChatCompletionService.class,
                ChatCompletionService.builder()
                    .withOpenAIAsyncClient(client)
                    .withModelId("gpt-35-turbo-2")
                    .build())
            .build();
        /////////////////////////////////////////////////////////

        /////////////////////////////////////////////////////////
        // Kernel with custom HttpClient
        HttpClient httpClient = HttpClient.createDefault();

        OpenAIAsyncClient client2 = new OpenAIClientBuilder()
            .httpClient(httpClient)
            .credential(new KeyCredential("a-key"))
            .buildAsyncClient();

        TextGenerationService textGenerationService = TextGenerationService.builder()
            .withOpenAIAsyncClient(client2)
            .withModelId("text-davinci-003")
            .build();

        Kernel kernel2 = Kernel.builder()
            .withAIService(TextGenerationService.class, textGenerationService)
            .build();
        /////////////////////////////////////////////////////////

        /////////////////////////////////////////////////////////
        //Plugins may also be configured via the corresponding Plugins property

        Kernel kernel3 = Kernel.builder()
            .withPlugin(KernelPluginFactory.createFromObject(new ConversationSummaryPlugin(),
                "ConversationSummaryPlugin"))
            .build();

        /////////////////////////////////////////////////////////
        // KernelBuilder provides a convenient API for creating Kernel instances. However, it is just a
        // wrapper, ultimately constructing a Kernel
        // using the public constructor that's available for anyone to use directly if desired.
        Kernel kernel = new Kernel(
            new OrderedAIServiceSelector(),
            new KernelPluginCollection()
        );
    }
}
