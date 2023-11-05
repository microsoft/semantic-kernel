// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.samples.syntaxexamples;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.SamplesConfig;
import com.microsoft.semantickernel.connectors.memory.azurecognitivesearch.AzureCognitiveSearchMemoryStore;
import com.microsoft.semantickernel.memory.VolatileMemoryStore;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;


/**
 * Demonstrate two examples about SK Semantic Memory:
 *
 * 1. Memory using Azure Cognitive Search.
 * 2. Memory using a custom embedding generator and vector engine.
 *
 * Semantic Memory allows to store your data like traditional DBs,
 * adding the ability to query it using natural language.
 * <p>
 * You must <a href=
 * "https://learn.microsoft.com/en-us/azure/search/search-create-service-portal">
 * create an Azure Cognitive Search service in the portal</a> to run this example.
 * <p>
 * Refer to the <a href=
 * "https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/samples/sample-code/README.md">
 * README</a> for configuring your environment to run the examples.
 */
public class Example14_SemanticMemory {
    private static final String MEMORY_COLLECTION_NAME = "SKGitHub";

    public static void main(String[] args) throws Exception {
        System.out.println("==============================================================");
        System.out.println("======== Semantic Memory using Azure Cognitive Search ========");
        System.out.println("==============================================================");

      var openAIAsyncClient = SamplesConfig.getClient();

      /* This example leverages Azure Cognitive Search to provide SK with Semantic Memory.
         *
         * Azure Cognitive Search automatically indexes your data semantically, so you don't
         * need to worry about embedding generation.
         */
      var kernelWithACS = SKBuilders.kernel()
          .withMemoryStorage(
              new AzureCognitiveSearchMemoryStore(System.getenv("ACS_ENDPOINT"), System.getenv("ACS_API_KEY")))
          .withDefaultAIService(SKBuilders.textEmbeddingGeneration()
              .withOpenAIClient(openAIAsyncClient)
              .withModelId("text-embedding-ada-002")
              .build())
          .build();

        runExampleAsync(kernelWithACS).block();

        System.out.println("====================================================");
        System.out.println("======== Semantic Memory (volatile, in RAM) ========");
        System.out.println("====================================================");

        /* You can build your own semantic memory combining an Embedding Generator
         * with a Memory storage that supports search by similarity (ie semantic search).
         *
         * In this example we use a volatile memory, a local simulation of a vector DB.
         *
         * You can replace VolatileMemoryStore with Qdrant (see QdrantMemoryStore connector)
         * or implement your connectors for Pinecone, Vespa, Postgres + pgvector, SQLite VSS, etc.
         */

        var kernelWithCustomDb = SKBuilders.kernel()
                .withDefaultAIService(SKBuilders.textEmbeddingGeneration()
                        .withOpenAIClient(openAIAsyncClient)
                        .withModelId("text-embedding-ada-002")
                        .build())
                .withMemoryStorage(new VolatileMemoryStore.Builder().build())
                .build();

        runExampleAsync(kernelWithCustomDb).block();
    }

    public static Mono<Void> runExampleAsync(Kernel kernel) {
        return storeMemoryAsync(kernel)
                .then(searchMemoryAsync(kernel, "How do I get started?"))

                /*
                Output:

                Query: How do I get started?

                Result 1:
                  URL:     : https://github.com/microsoft/semantic-kernel/blob/main/README.md
                  Title    : README: Installation, getting started, and how to contribute

                Result 2:
                  URL:     : https://github.com/microsoft/semantic-kernel/blob/main/samples/dotnet-jupyter-notebooks/00-getting-started.ipynb
                  Title    : Jupyter notebook describing how to get started with the Semantic Kernel

                */

                .then(searchMemoryAsync(kernel, "Can I build a chat with SK?"));

        /*
        Output:

        Query: Can I build a chat with SK?

        Result 1:
          URL:     : https://github.com/microsoft/semantic-kernel/tree/main/samples/skills/ChatSkill/ChatGPT
          Title    : Sample demonstrating how to create a chat skill interfacing with ChatGPT

        Result 2:
          URL:     : https://github.com/microsoft/semantic-kernel/blob/main/samples/apps/chat-summary-webapp-react/README.md
          Title    : README: README associated with a sample chat summary react-based webapp

        */
    }

    private static Mono<Void> searchMemoryAsync(Kernel kernel, String query) {
        return kernel.getMemory().searchAsync(MEMORY_COLLECTION_NAME, query, 2, 0.5f, false)
                .mapNotNull(memories -> {
                    System.out.println("\nQuery: " + query + "\n");
                    for (int n = 0; n < memories.size(); n++) {
                        var memory = memories.get(n);
                        System.out.println("Result " + (n + 1) + ":");
                        System.out.println("  URL:     : " + memory.getMetadata().getId());
                        System.out.println("  Title    : " + memory.getMetadata().getDescription());
                        System.out.println();
                    }
                    System.out.println("----------------------");
                    return null;
                });
    }

    private static Mono<Void> storeMemoryAsync(Kernel kernel) {
        /* Store some data in the semantic memory.
         *
         * When using Azure Cognitive Search the data is automatically indexed on write.
         *
         * When using the combination of VolatileStore and Embedding generation, SK takes
         * care of creating and storing the index
         */

        return Flux.fromIterable(sampleData().entrySet())
                .doFirst(() -> System.out.println("\nAdding some GitHub file URLs and their descriptions to the semantic memory."))
                .map(entry -> {
                            System.out.println("Save '" + entry.getKey() + "' to memory.");
                            return kernel.getMemory().saveReferenceAsync(
                                    MEMORY_COLLECTION_NAME,
                                    entry.getValue(),
                                    entry.getKey(),
                                    "GitHub",
                                    entry.getValue(),
                                    null);
                        }
                )
                .mapNotNull(Mono::block)
                .doFinally(signalType -> System.out.println("\n----------------------"))
                .then();
    }

    private static Map<String, String> sampleData() {
        return Arrays.stream(new String[][]{
                {"https://github.com/microsoft/semantic-kernel/blob/main/README.md", "README: Installation, getting started, and how to contribute"},
                {"https://github.com/microsoft/semantic-kernel/blob/main/samples/notebooks/dotnet/02-running-prompts-from-file.ipynb", "Jupyter notebook describing how to pass prompts from a file to a semantic skill or function"},
                {"https://github.com/microsoft/semantic-kernel/blob/main/samples/notebooks/dotnet/00-getting-started.ipynb", "Jupyter notebook describing how to get started with the Semantic Kernel"},
                {"https://github.com/microsoft/semantic-kernel/tree/main/samples/skills/ChatSkill/ChatGPT", "Sample demonstrating how to create a chat skill interfacing with ChatGPT"},
                {"https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel/Memory/VolatileMemoryStore.cs", "C# class that defines a volatile embedding store"},
                {"https://github.com/microsoft/semantic-kernel/blob/main/samples/dotnet/KernelHttpServer/README.md", "README: How to set up a Semantic Kernel Service API using Azure Function Runtime v4"},
                {"https://github.com/microsoft/semantic-kernel/blob/main/samples/apps/chat-summary-webapp-react/README.md", "README: README associated with a sample chat summary react-based webapp"},
        }).collect(Collectors.toMap(element -> element[0], element -> element[1]));
    }
}
