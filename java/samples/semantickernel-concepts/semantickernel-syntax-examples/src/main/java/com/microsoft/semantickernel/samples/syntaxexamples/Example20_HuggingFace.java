// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.core.credential.AzureKeyCredential;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.aiservices.huggingface.HuggingFaceClient;
import com.microsoft.semantickernel.aiservices.huggingface.services.HuggingFaceTextGenerationService;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionFromPrompt;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;

public class Example20_HuggingFace {

    private static final String HUGGINGFACE_CLIENT_KEY = System.getenv("HUGGINGFACE_CLIENT_KEY");
    private static final String HUGGINGFACE_CLIENT_ENDPOINT = System.getenv(
        "HUGGINGFACE_CLIENT_ENDPOINT");

    public static void main(String[] args) {
        //runConversationApiExampleAsync();
        runInferenceApiExampleAsync();
    }

    public static void runInferenceApiExampleAsync() {
        System.out.println("\n======== HuggingFace Inference API example ========\n");

        HuggingFaceClient client = HuggingFaceClient.builder()
            .credential(new AzureKeyCredential(HUGGINGFACE_CLIENT_KEY))
            .endpoint(HUGGINGFACE_CLIENT_ENDPOINT)
            .build();

        var chatCompletion = HuggingFaceTextGenerationService.builder()
            .withModelId("gpt2-24")
            .withHuggingFaceClient(client)
            .build();

        Kernel kernel = Kernel.builder()
            .withAIService(TextGenerationService.class, chatCompletion)
            .build();

        var questionAnswerFunction = KernelFunctionFromPrompt.builder()
            .withTemplate("Question: {{$input}}; Answer:")
            .build();

        var result = kernel.invokeAsync(questionAnswerFunction)
            .withArguments(
                KernelFunctionArguments.builder()
                    .withVariable("input", "What is New York?")
                    .build())
            .withResultType(String.class)
            .block();

        System.out.println(result.getResult());
    }

    /*
     * 
     * public static void runConversationApiExampleAsync() {
     * System.out.println("\n======== HuggingFace Inference API example ========\n");
     * 
     * HuggingFaceClient client = HuggingFaceClient.builder()
     * .credential(new AzureKeyCredential(HUGGINGFACE_CLIENT_KEY))
     * .endpoint(HUGGINGFACE_CLIENT_ENDPOINT)
     * .build();
     * 
     * var chatCompletion = HuggingFaceChatCompletionService.builder()
     * .withModelId("msft-dialogpt-medium-13")
     * .withHuggingFaceClient(client)
     * .build();
     * 
     * Kernel kernel = Kernel.builder()
     * .withAIService(ChatCompletionService.class, chatCompletion)
     * .build();
     * 
     * var questionAnswerFunction = KernelFunctionFromPrompt.builder()
     * .withTemplate("""
     * <message role="system">Assistant is a large language model that answers questions.</message>
     * <message role="assistant">What is your question?</message>
     * <message role="user">{{$input}}</message>
     * """)
     * .build();
     * 
     * var result = kernel.invokeAsync(questionAnswerFunction)
     * .withArguments(
     * KernelFunctionArguments.builder()
     * .withVariable("input", "What is New York?")
     * .build()
     * )
     * .withResultType(String.class)
     * .block();
     * 
     * System.out.println(result.getResult());
     * }
     * 
     */
}
