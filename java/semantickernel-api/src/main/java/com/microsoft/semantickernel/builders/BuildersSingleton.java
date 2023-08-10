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
import com.microsoft.semantickernel.textcompletion.CompletionSKFunction;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Supplier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Enum singleton that service loads builder implementations */
@SuppressWarnings("ImmutableEnumChecker")
public enum BuildersSingleton {
    INST;

    // Fallback classes in case the META-INF/services directory is missing
    private static final String FALLBACK_COMPLETION_FUNCTION_BUILDER_CLASS =
            "com.microsoft.semantickernel.orchestration.DefaultCompletionSKFunction$Builder";
    private static final String FALLBACK_KERNEL_BUILDER_CLASS =
            "com.microsoft.semantickernel.DefaultKernel$Builder";
    private static final String FALLBACK_TEXT_COMPLETION_BUILDER_CLASS =
            "com.microsoft.semantickernel.connectors.ai.openai.textcompletion.OpenAITextCompletion$Builder";
    private static final String FALLBACK_TEXT_EMBEDDING_GENERATION_BUILDER_CLASS =
            "com.microsoft.semantickernel.connectors.ai.openai.textembeddings.OpenAITextEmbeddingGeneration$Builder";
    private static final String FALLBACK_SKILL_COLLECTION_BUILDER_CLASS =
            "com.microsoft.semantickernel.skilldefinition.DefaultSkillCollection$Builder";
    private static final String FALLBACK_PROMPT_TEMPLATE_BUILDER_CLASS =
            "com.microsoft.semantickernel.semanticfunctions.DefaultPromptTemplate$Builder";
    private static final String FALLBACK_VARIABLE_BUILDER_CLASS =
            "com.microsoft.semantickernel.orchestration.DefaultContextVariables$Builder";
    private static final String FALLBACK_CONTEXT_BUILDER_CLASS =
            "com.microsoft.semantickernel.orchestration.DefaultSKContext$Builder";
    private static final String FALLBACK_PROMPT_TEMPLATE_ENGINE_BUILDER_CLASS =
            "com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine$Builder";
    private static final String FALLBACK_SEMANTIC_TEXT_MEMORY_CLASS =
            "com.microsoft.semantickernel.memory.DefaultSemanticTextMemory$Builder";
    private static final String FALLBACK_CHAT_COMPLETION_BUILDER_CLASS =
            "com.microsoft.semantickernel.connectors.ai.openai.chatcompletion.OpenAIChatCompletion$Builder";
    private static final String FALLBACK_MEMORY_STORE_BUILDER_CLASS =
            "com.microsoft.semantickernel.memory.VolatileMemoryStore$Builder";

    private final Map<Class<? extends SemanticKernelBuilder>, Supplier<? extends Buildable>>
            builders = new HashMap<>();

    BuildersSingleton() {
        try {
            registerBuilder(
                    CompletionSKFunction.Builder.class, FALLBACK_COMPLETION_FUNCTION_BUILDER_CLASS);
            registerBuilder(Kernel.Builder.class, FALLBACK_KERNEL_BUILDER_CLASS);
            registerBuilder(TextCompletion.Builder.class, FALLBACK_TEXT_COMPLETION_BUILDER_CLASS);
            registerBuilder(
                    EmbeddingGeneration.Builder.class,
                    FALLBACK_TEXT_EMBEDDING_GENERATION_BUILDER_CLASS);
            registerBuilder(
                    ReadOnlySkillCollection.Builder.class, FALLBACK_SKILL_COLLECTION_BUILDER_CLASS);

            registerBuilder(PromptTemplate.Builder.class, FALLBACK_PROMPT_TEMPLATE_BUILDER_CLASS);
            registerBuilder(ContextVariables.Builder.class, FALLBACK_VARIABLE_BUILDER_CLASS);

            registerBuilder(SemanticTextMemory.Builder.class, FALLBACK_SEMANTIC_TEXT_MEMORY_CLASS);

            registerBuilder(SKContext.Builder.class, FALLBACK_CONTEXT_BUILDER_CLASS);
            registerBuilder(
                    PromptTemplateEngine.Builder.class,
                    FALLBACK_PROMPT_TEMPLATE_ENGINE_BUILDER_CLASS);

            registerBuilder(ChatCompletion.Builder.class, FALLBACK_CHAT_COMPLETION_BUILDER_CLASS);
            registerBuilder(MemoryStore.Builder.class, FALLBACK_MEMORY_STORE_BUILDER_CLASS);
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

    private <U extends Buildable, T extends SemanticKernelBuilder<U>> void registerBuilder(
            Class<T> clazz, String fallbackClassName) {
        builders.put(
                clazz,
                (Supplier<? extends Buildable>)
                        ServiceLoadUtil.findServiceLoader(clazz, fallbackClassName));
    }

    public <U extends Buildable, T extends SemanticKernelBuilder<U>> T getInstance(Class<T> clazz) {
        return (T) builders.get(clazz).get();
    }

    /**
     * Builder for creating a {@link TextCompletion}
     *
     * @return a {@link TextCompletion.Builder}
     */
    public TextCompletion.Builder getTextCompletionBuilder() {
        return getInstance(TextCompletion.Builder.class);
    }

    /**
     * Builder for creating a {@link EmbeddingGeneration}
     *
     * @return a {@link EmbeddingGeneration.Builder}
     */
    public EmbeddingGeneration.Builder<String> getTextEmbeddingGenerationBuilder() {
        return getInstance(EmbeddingGeneration.Builder.class);
    }

    /**
     * Builder for creating a {@link ReadOnlySkillCollection}
     *
     * @return a {@link ReadOnlySkillCollection.Builder}
     */
    public ReadOnlySkillCollection.Builder getReadOnlySkillCollection() {
        return getInstance(ReadOnlySkillCollection.Builder.class);
    }

    /**
     * Builder for creating a {@link PromptTemplate}
     *
     * @return a {@link PromptTemplate.Builder}
     */
    public PromptTemplate.Builder getPromptTemplateBuilder() {
        return getInstance(PromptTemplate.Builder.class);
    }

    /**
     * Builder for creating a {@link PromptTemplateEngine}
     *
     * @return a {@link PromptTemplateEngine.Builder}
     */
    public PromptTemplateEngine.Builder getPromptTemplateEngineBuilder() {
        return getInstance(PromptTemplateEngine.Builder.class);
    }

    /**
     * Builder for creating a {@link ContextVariables}
     *
     * @return a {@link ContextVariables.Builder}
     */
    public ContextVariables.Builder variables() {
        return getInstance(ContextVariables.Builder.class);
    }

    /**
     * Builder for creating a {@link SKContext}
     *
     * @return a {@link SKContext.Builder}
     */
    public SKContext.Builder context() {
        return getInstance(SKContext.Builder.class);
    }

    /**
     * Builder for creating a {@link SemanticTextMemory}
     *
     * @return a {@link SemanticTextMemory.Builder}
     */
    public SemanticTextMemory.Builder getSemanticTextMemoryBuilder() {
        return getInstance(SemanticTextMemory.Builder.class);
    }

    /**
     * Builder for creating a {@link ChatCompletion}
     *
     * @return a {@link ChatCompletion.Builder}
     */
    public ChatCompletion.Builder getChatCompletion() {
        return getInstance(ChatCompletion.Builder.class);
    }

    /**
     * Builder for creating a {@link MemoryStore}
     *
     * @return a {@link MemoryStore.Builder}
     */
    public MemoryStore.Builder getMemoryStoreBuilder() {
        return getInstance(MemoryStore.Builder.class);
    }
}
