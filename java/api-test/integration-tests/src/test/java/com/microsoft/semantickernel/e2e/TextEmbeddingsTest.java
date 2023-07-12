// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.e2e;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.connectors.ai.openai.textembeddings.OpenAITextEmbeddingGeneration;
import com.microsoft.semantickernel.coreskills.TextMemorySkill;
import com.microsoft.semantickernel.memory.MemoryQueryResult;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.memory.VolatileMemoryStore;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIf;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class TextEmbeddingsTest extends AbstractKernelTest {

    private static final Logger LOGGER = LoggerFactory.getLogger(TextEmbeddingsTest.class);
    private static final int EXPECTED_EMBEDDING_SIZE = 1536;

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void testEmbeddingGenerationOpenAI() throws IOException {
        OpenAIAsyncClient client = getOpenAIClient();
        String model = "text-embedding-ada-002";
        OpenAITextEmbeddingGeneration embeddingGeneration =
                new OpenAITextEmbeddingGeneration(client, model);

        List<String> data = new ArrayList<>();
        data.add("This is just");
        //data.add("a test");

        embeddingGeneration
                .generateEmbeddingsAsync(data)
                .block()
                .forEach(
                        embedding ->
                                Assertions.assertEquals(
                                        EXPECTED_EMBEDDING_SIZE, embedding.getVector().size()));
    }

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void testEmbeddingGeneration() throws IOException {
        String model = "text-embedding-ada-002";
        OpenAITextEmbeddingGeneration embeddingGeneration =
                new OpenAITextEmbeddingGeneration(getOpenAIClient(), model);

        List<String> data = new ArrayList<>();
        data.add("This is just a test");

        LOGGER.info(String.valueOf(embeddingGeneration.generateEmbeddingsAsync(data).block()));
    }

    @Test
    @EnabledIf("isAzureTestEnabled")
    public void testMemory() throws IOException {

        Kernel kernel = buildTextCompletionKernel();
        kernel.importSkill(new TextMemorySkill(), "aboutMe");

        String skPrompt =
                """

                        ChatBot can have a conversation with you about any topic.
                        It can give explicit instructions or say 'I don't know' if it does not have an answer.

                        Information about me, from previous conversations:
                        - {{$fact1}} {{recall $fact1}}
                        - {{$fact2}} {{recall $fact2}}
                        - {{$fact3}} {{recall $fact3}}
                        - {{$fact4}} {{recall $fact4}}
                        - {{$fact5}} {{recall $fact5}}

                        Chat:
                        {{$history}}
                        User: {{$userInput}}
                        ChatBot:\s""";

        CompletionSKFunction chat =
                kernel.getSemanticFunctionBuilder()
                        .createFunction(
                                skPrompt, "recall", "aboutMe", "TextEmbeddingTest#testMemory");

        VolatileMemoryStore volatileMemoryStore = new VolatileMemoryStore();
        volatileMemoryStore.createCollectionAsync("aboutMe").block();

        OpenAITextEmbeddingGeneration embeddingGeneration =
                new OpenAITextEmbeddingGeneration(getOpenAIClient(), "text-embedding-ada-002");

        SemanticTextMemory memory =
                SKBuilders.semanticTextMemory()
                        .setEmbeddingGenerator(embeddingGeneration)
                        .setStorage(volatileMemoryStore)
                        .build();

        SKContext context =
                SKBuilders.context()
                        .with(SKBuilders.variables().build())
                        .with(memory)
                        .with(kernel.getSkills())
                        .build();

        context.getSemanticMemory()
                .saveInformationAsync("aboutMe", "My name is Andrea", "fact1", null, null)
                .block();

        context.getSemanticMemory()
                .saveInformationAsync(
                        "aboutMe", "I currently work as a tour guide", "fact2", null, null)
                .block();

        context.getSemanticMemory()
                .saveInformationAsync(
                        "aboutMe", "I've been living in Seattle since 2005", "fact3", null, null)
                .block();

        context.getSemanticMemory()
                .saveInformationAsync(
                        "aboutMe",
                        "I visited France and Italy five times since 2015",
                        "fact4",
                        null,
                        null)
                .block();

        context.getSemanticMemory()
                .saveInformationAsync("aboutMe", "My family is from New York", "fact5", null, null)
                .block();

        String query = "Where are you from originally?";
        List<MemoryQueryResult> results =
                memory.searchAsync("aboutMe", query, 10, .5, false).block();
        results.forEach(
                result ->
                        System.out.printf(
                                "%s %s (relevance=%f)%n",
                                query, result.getMetadata().getText(), result.getRelevance()));
    }

}
