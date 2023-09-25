// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.azure.ai.openai.OpenAIAsyncClient;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.ai.embeddings.TextEmbeddingGeneration;
import com.microsoft.semantickernel.coreskills.TextMemorySkill;
import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.VolatileMemoryStore;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.util.List;
import java.util.stream.Collectors;
import reactor.core.publisher.Mono;

public class Example15_MemorySkill {
    private static final String MEMORY_COLLECTION_NAME = "aboutMe";

    public static void main(String[] args) {
        runAsync().block();
    }

    public static Mono<Void> runAsync() {
        // ========= Create a kernel =========
        OpenAIAsyncClient client = null;
        try {
            client = SamplesConfig.getClient();
        } catch (Exception e) {
            return Mono.error(e);
        }

        TextCompletion textCompletionService =
                SKBuilders.textCompletion()
                        .withModelId("text-davinci-003")
                        .withOpenAIClient(client)
                        .build();

        TextEmbeddingGeneration textEmbeddingGenerationService =
                SKBuilders.textEmbeddingGeneration()
                        .withOpenAIClient(client)
                        .withModelId("text-embedding-ada-002")
                        .build();

        MemoryStore memoryStore = new VolatileMemoryStore.Builder().build();

        Kernel kernel = SKBuilders.kernel()
                .withDefaultAIService(textCompletionService)
                .withDefaultAIService(textEmbeddingGenerationService)
                .withMemoryStorage(memoryStore)
                .build();

        // ========= Store memories using the kernel =========

        kernel.getMemory().saveInformationAsync(MEMORY_COLLECTION_NAME, "My name is Andrea", "info1", null, null).block();
        kernel.getMemory().saveInformationAsync(MEMORY_COLLECTION_NAME, "I work as a tourist operator", "info2", null, null).block();
        kernel.getMemory().saveInformationAsync(MEMORY_COLLECTION_NAME, "I've been living in Seattle since 2005", "info3", null, null).block();
        kernel.getMemory().saveInformationAsync(MEMORY_COLLECTION_NAME, "I visited France and Italy five times since 2015", "info4", null, null).block();

        // ========= Store memories using semantic function =========

        // Add Memory as a skill for other functions
        TextMemorySkill memorySkill = new TextMemorySkill();
        kernel.importSkill(memorySkill, "memory");

        // Build a semantic function that saves info to memory
        PromptTemplateConfig.CompletionConfig completionConfig = SKBuilders.completionConfig()
                .temperature(0.2)
                .topP(0.5)
                .presencePenalty(0)
                .frequencyPenalty(0)
                .maxTokens(2000)
                .build();

        CompletionSKFunction saveFunctionDefinition = SKBuilders.completionFunctions()
                .withKernel(kernel)
                .withPromptTemplate("{{memory.save $info}}")
                .withFunctionName("save")
                .withDescription("save information to memory")
                .withCompletionConfig(completionConfig)
                .build();

        CompletionSKFunction memorySaver =
                kernel.registerSemanticFunction(saveFunctionDefinition);

        SKContext context = SKBuilders.context()
                .withMemory(kernel.getMemory())
                .withSkills(kernel.getSkills())
                .build();

        context.setVariable(TextMemorySkill.COLLECTION_PARAM, MEMORY_COLLECTION_NAME)
                .setVariable(TextMemorySkill.KEY_PARAM, "info5")
                .setVariable(TextMemorySkill.INFO_PARAM, "My family is from New York");

        memorySaver.invokeAsync(context).block();

        // ========= Test memory remember =========
        System.out.println("========= Example: Recalling a Memory =========");

        // create a new context to avoid using the variables from the previous example
        context = SKBuilders.context()
                .withMemory(kernel.getMemory())
                .withSkills(kernel.getSkills())
                .build();

        String answer = memorySkill.retrieveAsync(MEMORY_COLLECTION_NAME, "info1", context).block();
        System.out.printf("Memory associated with 'info1': %s%n", answer);
        /*
        Output:
        "Memory associated with 'info1': My name is Andrea
        */

        // ========= Test memory recall =========
        System.out.println("========= Example: Recalling an Idea =========");

        List<String> answers = memorySkill.recallAsync(
                "Where did I grow up?",
                MEMORY_COLLECTION_NAME,
                0,
                2,
                context).block();

        System.out.println("Ask: Where did I grow up?");
        System.out.printf("Answer:%n\t%s%n", answers.stream().collect(Collectors.joining("\",\"", "[\"", "\"]")));

        answers = memorySkill.recallAsync(
                "Where do I live?",
                MEMORY_COLLECTION_NAME,
                0,
                2,
                context).block();

        System.out.println("Ask: Where do I live?");
        System.out.printf("Answer:%n\t%s%n", answers.stream().collect(Collectors.joining("\",\"", "[\"", "\"]")));

        /*
        Output:

            Ask: where did I grow up?
            Answer:
                ["My family is from New York","I've been living in Seattle since 2005"]

            Ask: where do I live?
            Answer:
                ["I've been living in Seattle since 2005","My family is from New York"]
        */

        // ========= Use memory in a semantic function =========
        System.out.println("========= Example: Using Recall in a Semantic Function =========");

        // Build a semantic function that uses memory to find facts
        String prompt =
                "Consider only the facts below when answering questions.\n" +
                        "About me: {{memory.recall 'where did I grow up?'}}\n" +
                        "About me: {{memory.recall 'where do I live?'}}\n" +
                        "Question: {{$input}}\n" +
                        "Answer: ";

        CompletionSKFunction recallFunctionDefinition = SKBuilders.completionFunctions()
                .withKernel(kernel)
                .withPromptTemplate(prompt)
                .withCompletionConfig(completionConfig)
                .build();

        SKFunction<?> aboutMeOracle = kernel.registerSemanticFunction(recallFunctionDefinition);

        context.setVariable(TextMemorySkill.COLLECTION_PARAM, MEMORY_COLLECTION_NAME)
                .setVariable(TextMemorySkill.RELEVANCE_PARAM, "0.75");

        SKContext result = aboutMeOracle.invokeAsync("Do I live in the same town where I grew up?", context, null).block();

        System.out.println("Do I live in the same town where I grew up?\n");
        System.out.println(result.getResult());

        /*
        Output:

            Do I live in the same town where I grew up?

            No, I do not live in the same town where I grew up since my family is from New York and I have been living in Seattle since 2005.
        */

        // ========= Remove a memory =========
        System.out.println("========= Example: Forgetting a Memory =========");

        context.setVariable("fact1", "What is my name?")
                .setVariable("fact2", "What do I do for a living?")
                .setVariable(TextMemorySkill.RELEVANCE_PARAM, "0.75");

        result = aboutMeOracle.invokeAsync("Tell me a bit about myself", context, null).block();

        System.out.println("Tell me a bit about myself\n");
        System.out.println(result.getResult());

        /*
        Approximate Output:
            Tell me a bit about myself

            My name is Andrea and my family is from New York. I work as a tourist operator.
        */

        memorySkill.removeAsync(MEMORY_COLLECTION_NAME, "info1", context).block();

        result = aboutMeOracle.invokeAsync("Tell me a bit about myself", context, null).block();

        System.out.println("Tell me a bit about myself\n");
        System.out.println(result.getResult());

        /*
        Approximate Output:
            Tell me a bit about myself

            I'm from a family originally from New York and I work as a tourist operator. I've been living in Seattle since 2005.
        */

        return Mono.empty();
    }
}
