// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.azure.core.exception.HttpResponseException;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.hooks.FunctionInvokedEvent;
import com.microsoft.semantickernel.hooks.FunctionInvokingEvent;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.hooks.PromptRenderedEvent;
import com.microsoft.semantickernel.hooks.PromptRenderingEvent;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.services.AIService;
import com.microsoft.semantickernel.services.AIServiceSelection;
import com.microsoft.semantickernel.services.TextAIService;
import com.microsoft.semantickernel.services.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.services.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.services.textcompletion.TextGenerationService;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * A {@link KernelFunction} implementation that is created from a prompt template.
 *
 * @param <T> the type of the return value of the function
 */
public class KernelFunctionFromPrompt<T> extends KernelFunction<T> {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelFunctionFromPrompt.class);

    private final PromptTemplate template;

    /**
     * Creates a new instance of {@link KernelFunctionFromPrompt}.
     *
     * @param template          the prompt template to use for the function
     * @param promptConfig      the configuration for the prompt
     * @param executionSettings the execution settings to use when invoking the function
     */
    protected KernelFunctionFromPrompt(
        PromptTemplate template,
        PromptTemplateConfig promptConfig,
        @Nullable Map<String, PromptExecutionSettings> executionSettings) {
        super(
            new KernelFunctionMetadata<>(
                null,
                getName(promptConfig),
                promptConfig.getDescription(),
                promptConfig.getKernelParametersMetadata(),
                promptConfig.getKernelReturnParameterMetadata()),
            executionSettings != null ? executionSettings : promptConfig.getExecutionSettings());
        this.template = template;
    }

    private static String getName(PromptTemplateConfig promptConfig) {
        if (promptConfig.getName() == null) {
            return UUID.randomUUID().toString();
        } else {
            return promptConfig.getName();
        }
    }

    /**
     * Creates a new instance of {@link Builder}.
     *
     * @param <T> The type of the return value of the function
     * @return a new instance of {@link Builder}
     */
    public static <T> Builder<T> builder() {
        return new Builder<>();
    }

    /**
     * Creates a new instance of {@link Builder}.
     *
     * @param returnType The type of the return value of the function
     * @param <T>        The type of the return value of the function
     * @return a new instance of {@link Builder}
     */
    public static <T> Builder<T> builder(Class<T> returnType) {
        return new Builder<>();
    }

    private Flux<FunctionResult<T>> invokeInternalAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments argumentsIn,
        @Nullable ContextVariableType<T> contextVariableType,
        @Nullable InvocationContext invocationContext) {

        InvocationContext context = invocationContext != null ? invocationContext
            : InvocationContext.builder().build();

        // must be effectively final for lambda
        KernelHooks kernelHooks = context.getKernelHooks() != null
            ? context.getKernelHooks()
            : kernel.getGlobalKernelHooks();
        assert kernelHooks != null : "getGlobalKernelHooks() should never return null";

        PromptRenderingEvent preRenderingHookResult = kernelHooks
            .executeHooks(new PromptRenderingEvent(this, argumentsIn));

        KernelFunctionArguments arguments = preRenderingHookResult.getArguments();

        // TODO: put in method, add catch for classcastexception, fallback to noopconverter
        ContextVariableType<T> variableType = contextVariableType != null
            ? contextVariableType
            : context.getContextVariableTypes().getVariableTypeForClass(
                (Class<T>) this.getMetadata().getOutputVariableType().getType());

        return this.template
            .renderAsync(kernel, arguments, context)
            .flatMapMany(prompt -> {
                PromptRenderedEvent promptHookResult = kernelHooks
                    .executeHooks(new PromptRenderedEvent(this, arguments, prompt));
                prompt = promptHookResult.getPrompt();
                KernelFunctionArguments args = promptHookResult.getArguments();

                LOGGER.info("RENDERED PROMPT: \n{}", prompt);

                FunctionInvokingEvent updateArguments = kernelHooks
                    .executeHooks(new FunctionInvokingEvent(this, args));
                args = updateArguments.getArguments();

                AIServiceSelection<?> aiServiceSelection = kernel
                    .getServiceSelector()
                    .trySelectAIService(
                        TextAIService.class,
                        this,
                        args);

                AIService client = aiServiceSelection != null ? aiServiceSelection.getService()
                    : null;
                if (aiServiceSelection == null) {
                    throw new IllegalStateException(
                        "Failed to initialise aiService, could not find any TextAIService implementations");
                }

                Flux<FunctionResult<T>> result;

                // settings from prompt or use default
                PromptExecutionSettings executionSettings = aiServiceSelection.getSettings();

                if (client instanceof ChatCompletionService) {
                    InvocationContext contextWithExecutionSettings = context;
                    if (context.getPromptExecutionSettings() == null) {
                        contextWithExecutionSettings = InvocationContext.copy(context)
                            .withPromptExecutionSettings(executionSettings)
                            .build();
                    }

                    result = ((ChatCompletionService) client)
                        .getChatMessageContentsAsync(
                            prompt,
                            kernel,
                            contextWithExecutionSettings)
                        .flatMapMany(Flux::fromIterable)
                        .concatMap(chatMessageContent -> {
                            if (chatMessageContent.getAuthorRole() == AuthorRole.ASSISTANT) {

                                T value = variableType
                                    .getConverter()
                                    .fromObject(chatMessageContent);

                                if (value == null) {
                                    value = variableType
                                        .getConverter()
                                        .fromPromptString(
                                            chatMessageContent.getContent());
                                }

                                return Flux.just(
                                    new FunctionResult<>(
                                        new ContextVariable<>(variableType, value),
                                        chatMessageContent.getMetadata(),
                                        chatMessageContent));
                            }
                            return Flux.empty();
                        })
                        .map(it -> {
                            return new FunctionResult<>(
                                new ContextVariable<>(
                                    variableType,
                                    it.getResult() != null
                                        ? variableType.of(it.getResult()).getValue()
                                        : null),
                                it.getMetadata(),
                                it.getUnconvertedResult());
                        });
                } else if (client instanceof TextGenerationService) {
                    result = ((TextGenerationService) client)
                        .getTextContentsAsync(
                            prompt,
                            executionSettings,
                            kernel)
                        .flatMapMany(Flux::fromIterable)
                        .concatMap(textContent -> {
                            T value = variableType
                                .getConverter()
                                .fromObject(textContent);

                            if (value == null) {
                                value = variableType
                                    .getConverter()
                                    .fromPromptString(textContent.getContent());
                            }

                            return Flux.just(
                                new FunctionResult<>(
                                    new ContextVariable<>(
                                        variableType,
                                        value),
                                    textContent.getMetadata(),
                                    textContent));
                        });
                } else {
                    return Flux.error(new IllegalStateException("Unknown service type"));
                }

                return result
                    .map(it -> {
                        FunctionInvokedEvent<T> updatedResult = kernelHooks
                            .executeHooks(
                                new FunctionInvokedEvent<>(
                                    this,
                                    arguments,
                                    it));

                        return updatedResult.getResult();
                    });
            })
            .doOnError(
                ex -> {
                    LOGGER.warn(
                        "Something went wrong while rendering the semantic"
                            + " function or while executing the text"
                            + " completion. Function: {}.{}. Error: {}",
                        getPluginName(),
                        getName(),
                        ex.getMessage());

                    // Common message when you attempt to send text completion
                    // requests to a chat completion model:
                    //    "logprobs, best_of and echo parameters are not
                    // available on gpt-35-turbo model"
                    if (ex instanceof HttpResponseException
                        && ((HttpResponseException) ex).getResponse().getStatusCode() == 400
                        && ex.getMessage() != null
                        && ex.getMessage().contains("parameters are not available" + " on")) {
                        LOGGER.warn(
                            "This error indicates that you have attempted"
                                + " to use a chat completion model in a"
                                + " text completion service. Try using a"
                                + " chat completion service instead when"
                                + " building your kernel, for instance when"
                                + " building your service use"
                                + " SKBuilders.chatCompletion() rather than"
                                + " SKBuilders.textCompletionService().");
                    }
                });
    }

    @Override
    public Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> variableType,
        @Nullable InvocationContext invocationContext) {
        return invokeInternalAsync(kernel, arguments, variableType, invocationContext)
            .take(1).single();
    }

    /**
     * A builder for creating a {@link KernelFunction} from a prompt template.
     *
     * @param <T> the type of the return value of the function
     */
    public static final class Builder<T> implements FromPromptBuilder<T> {

        @Nullable
        private PromptTemplate promptTemplate;
        @Nullable
        private String name;
        @Nullable
        private Map<String, PromptExecutionSettings> executionSettings = null;
        @Nullable
        private String description;
        @Nullable
        private List<InputVariable> inputVariables;
        @Nullable
        private String template;
        private String templateFormat = PromptTemplateConfig.SEMANTIC_KERNEL_TEMPLATE_FORMAT;
        @Nullable
        private OutputVariable<?> outputVariable;
        @Nullable
        private PromptTemplateFactory promptTemplateFactory;
        @Nullable
        private PromptTemplateConfig promptTemplateConfig;

        @Override
        public FromPromptBuilder<T> withName(@Nullable String name) {
            this.name = name;
            return this;
        }

        @Override
        public FromPromptBuilder<T> withInputParameters(
            @Nullable List<InputVariable> inputVariables) {
            if (inputVariables != null) {
                this.inputVariables = new ArrayList<>(inputVariables);
            } else {
                this.inputVariables = null;
            }
            return this;
        }

        @Override
        public FromPromptBuilder<T> withPromptTemplate(@Nullable PromptTemplate promptTemplate) {
            this.promptTemplate = promptTemplate;
            return this;
        }

        @Override
        public FromPromptBuilder<T> withExecutionSettings(
            @Nullable Map<String, PromptExecutionSettings> executionSettings) {
            if (this.executionSettings == null) {
                this.executionSettings = new HashMap<>();
            }

            if (executionSettings != null) {
                this.executionSettings.putAll(executionSettings);
            }
            return this;
        }

        @Override
        public FromPromptBuilder<T> withDefaultExecutionSettings(
            @Nullable PromptExecutionSettings executionSettings) {
            if (executionSettings == null) {
                return this;
            }

            if (this.executionSettings == null) {
                this.executionSettings = new HashMap<>();
            }

            this.executionSettings.put(PromptExecutionSettings.DEFAULT_SERVICE_ID,
                executionSettings);

            if (executionSettings.getServiceId() != null) {
                this.executionSettings.put(executionSettings.getServiceId(), executionSettings);
            }
            return this;
        }

        @Override
        public FromPromptBuilder<T> withDescription(@Nullable String description) {
            this.description = description;
            return this;
        }

        @Override
        public FromPromptBuilder<T> withTemplate(@Nullable String template) {
            this.template = template;
            return this;
        }

        @Override
        public FromPromptBuilder<T> withTemplateFormat(String templateFormat) {
            this.templateFormat = templateFormat;
            return this;
        }

        @Override
        public <U> FromPromptBuilder<U> withOutputVariable(
            @Nullable OutputVariable<U> outputVariable) {
            this.outputVariable = outputVariable;
            return (FromPromptBuilder<U>) this;
        }

        @Override
        public FromPromptBuilder<T> withOutputVariable(@Nullable String description, String type) {
            return this.withOutputVariable(new OutputVariable(type, description));
        }

        @Override
        public FromPromptBuilder<T> withPromptTemplateFactory(
            @Nullable PromptTemplateFactory promptTemplateFactory) {
            this.promptTemplateFactory = promptTemplateFactory;
            return this;
        }

        @Override
        public FromPromptBuilder<T> withPromptTemplateConfig(
            @Nullable PromptTemplateConfig promptTemplateConfig) {
            this.promptTemplateConfig = promptTemplateConfig;
            return this;
        }

        @Override
        public KernelFunction<T> build() {

            if (templateFormat == null) {
                templateFormat = PromptTemplateConfig.SEMANTIC_KERNEL_TEMPLATE_FORMAT;
            }

            if (name == null) {
                name = UUID.randomUUID().toString();
            }

            if (promptTemplateFactory == null) {
                promptTemplateFactory = new KernelPromptTemplateFactory();
            }

            if (promptTemplateConfig != null) {
                if (promptTemplate == null) {
                    promptTemplate = promptTemplateFactory.tryCreate(promptTemplateConfig);
                }
                return new KernelFunctionFromPrompt<>(
                    promptTemplate,
                    promptTemplateConfig,
                    executionSettings);
            }

            PromptTemplateConfig config = new PromptTemplateConfig(
                name,
                template,
                templateFormat,
                description,
                inputVariables,
                outputVariable,
                executionSettings);

            PromptTemplate temp;
            if (promptTemplate != null) {
                temp = promptTemplate;
            } else {
                temp = new KernelPromptTemplateFactory().tryCreate(config);
            }

            return new KernelFunctionFromPrompt<>(temp, config, executionSettings);

        }

    }
}
