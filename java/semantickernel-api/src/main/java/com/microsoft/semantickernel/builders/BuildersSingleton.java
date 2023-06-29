// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Enum singleton that service loads builder implementations */
public enum BuildersSingleton {
    INST;

    // Fallback classes in case the META-INF/services directory is missing
    private static final String FALLBACK_FUNCTION_BUILDER_CLASS =
            "com.microsoft.semantickernel.SkFunctionBuilders";
    private static final String FALLBACK_KERNEL_BUILDER_CLASS =
            "com.microsoft.semantickernel.DefaultKernel$Builder";
    private static final String FALLBACK_TEXT_COMPLETION_BUILDER_CLASS =
            "com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion$Builder";

    private static final String FALLBACK_TEXT_EMBEDDING_GENERATION_BUILDER_CLASS =
            "com.microsoft.semantickernel.connectors.ai.openai.textembeddings.OpenAITextEmbeddingGeneration$Builder";
    private static final String FALLBACK_SKILL_COLLECTION_BUILDER_CLASS =
            "com.microsoft.semantickernel.skilldefinition.DefaultCollection$Builder";

    private static final String FALLBACK_PROMPT_TEMPLATE_BUILDER_CLASS =
            "com.microsoft.semantickernel.semanticfunctions.DefaultPromptTemplate$Builder";

    private static final String FALLBACK_VARIABLE_BUILDER_CLASS =
            "com.microsoft.semantickernel.orchestration.DefaultContextVariables$Builder";

    private static final String FALLBACK_CONTEXT_BUILDER_CLASS =
            "com.microsoft.semantickernel.orchestration.DefaultSemanticSKContext$Builder";
    private static final String FALLBACK_PROMPT_TEMPLATE_ENGINE_BUILDER_CLASS =
            "com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine$Builder";
    private static final String FALLBACK_SEMANTIC_TEXT_MEMORY_CLASS =
            "com.microsoft.semantickernel.memory.DefaultSemanticTextMemory$Builder";
    private static final String FALLBACK_CHAT_COMPLETION_BUILDER_CLASS =
            "com.microsoft.semantickernel.connectors.ai.openai.chatcompletion.OpenAIChatCompletion$Builder";

    private static final String FALLBACK_MEMORY_STORE_BUILDER_CLASS =
            "com.microsoft.semantickernel.memory.VolatileMemoryStore$Builder";

    private final FunctionBuilders functionBuilders;
    private final Kernel.InternalBuilder kernelBuilder;
    private final TextCompletion.Builder textCompletionBuilder;
    private final EmbeddingGeneration.Builder<String, Float> textEmbeddingGenerationBuilder;
    private final ReadOnlySkillCollection.Builder readOnlySkillCollection;
    private final PromptTemplate.Builder promptTemplate;
    private final ContextVariables.Builder variables;
    private final SKContext.Builder context;
    private final PromptTemplateEngine.Builder promptTemplateEngine;
    private final ChatCompletion.Builder chatCompletion;
    private final SemanticTextMemory.Builder semanticTextMemoryBuilder;
    private final MemoryStore.Builder memoryStoreBuilder;

    BuildersSingleton() {
        try {
            functionBuilders =
                    ServiceLoadUtil.findServiceLoader(
                            FunctionBuilders.class, FALLBACK_FUNCTION_BUILDER_CLASS);

            kernelBuilder =
                    ServiceLoadUtil.findServiceLoader(
                            Kernel.InternalBuilder.class, FALLBACK_KERNEL_BUILDER_CLASS);

            textCompletionBuilder =
                    ServiceLoadUtil.findServiceLoader(
                            TextCompletion.Builder.class, FALLBACK_TEXT_COMPLETION_BUILDER_CLASS);

            textEmbeddingGenerationBuilder =
                    ServiceLoadUtil.findServiceLoader(
                            EmbeddingGeneration.Builder.class,
                            FALLBACK_TEXT_EMBEDDING_GENERATION_BUILDER_CLASS);

            readOnlySkillCollection =
                    ServiceLoadUtil.findServiceLoader(
                            ReadOnlySkillCollection.Builder.class,
                            FALLBACK_SKILL_COLLECTION_BUILDER_CLASS);

            promptTemplate =
                    ServiceLoadUtil.findServiceLoader(
                            PromptTemplate.Builder.class, FALLBACK_PROMPT_TEMPLATE_BUILDER_CLASS);

            variables =
                    ServiceLoadUtil.findServiceLoader(
                            ContextVariables.Builder.class, FALLBACK_VARIABLE_BUILDER_CLASS);
            semanticTextMemoryBuilder =
                    ServiceLoadUtil.findServiceLoader(
                            SemanticTextMemory.Builder.class, FALLBACK_SEMANTIC_TEXT_MEMORY_CLASS);

            context =
                    ServiceLoadUtil.findServiceLoader(
                            SKContext.Builder.class, FALLBACK_CONTEXT_BUILDER_CLASS);

            promptTemplateEngine =
                    ServiceLoadUtil.findServiceLoader(
                            PromptTemplateEngine.Builder.class,
                            FALLBACK_PROMPT_TEMPLATE_ENGINE_BUILDER_CLASS);

            chatCompletion =
                    ServiceLoadUtil.findServiceLoader(
                            ChatCompletion.Builder.class, FALLBACK_CHAT_COMPLETION_BUILDER_CLASS);

            memoryStoreBuilder =
                    ServiceLoadUtil.findServiceLoader(
                            MemoryStore.Builder.class, FALLBACK_MEMORY_STORE_BUILDER_CLASS);

        } catch (Throwable e) {
            Logger LOGGER = LoggerFactory.getLogger(BuildersSingleton.class);
            LOGGER.error("Failed to discover Semantic Kernel Builders", e);
            LOGGER.error(
                    "This is likely due to:\n\n"
                        + "- The Semantic Kernel implementation (typically provided by"
                        + " semantickernel-core) is not present on the classpath at runtime, ensure"
                        + " that this dependency is available at runtime. In maven this would be"
                        + " achieved by adding:\n"
                        + "\n"
                        + "        <dependency>\n"
                        + "            <groupId>com.microsoft.semantickernel</groupId>\n"
                        + "            <artifactId>semantickernel-core</artifactId>\n"
                        + "            <version>${skversion}</version>\n"
                        + "            <scope>runtime</scope>\n"
                        + "        </dependency>\n\n"
                        + "- The META-INF/services files that define the service loading have been"
                        + " filtered out and are not present within the running application\n\n"
                        + "- The class names have been changed (for instance shaded) preventing"
                        + " discovering the classes");

            throw e;
        }
    }

    public FunctionBuilders getFunctionBuilders() {
        return functionBuilders;
    }

    public Kernel.InternalBuilder getKernelBuilder() {
        return kernelBuilder;
    }

    public TextCompletion.Builder getTextCompletionBuilder() {
        return textCompletionBuilder;
    }

    public EmbeddingGeneration.Builder<String, Float> getTextEmbeddingGenerationBuilder() {
        return textEmbeddingGenerationBuilder;
    }

    public ReadOnlySkillCollection.Builder getReadOnlySkillCollection() {
        return readOnlySkillCollection;
    }

    public PromptTemplate.Builder getPromptTemplateBuilder() {
        return promptTemplate;
    }

    public PromptTemplateEngine.Builder getPromptTemplateEngineBuilder() {
        return promptTemplateEngine;
    }

    public ContextVariables.Builder variables() {
        return variables;
    }

    public SKContext.Builder context() {
        return context;
    }

    public SemanticTextMemory.Builder getSemanticTextMemoryBuilder() {
        return semanticTextMemoryBuilder;
    }

    public ChatCompletion.Builder getChatCompletion() {
        return chatCompletion;
    }

    public MemoryStore.Builder getMemoryStoreBuilder() {
        return memoryStoreBuilder;
    }
}
