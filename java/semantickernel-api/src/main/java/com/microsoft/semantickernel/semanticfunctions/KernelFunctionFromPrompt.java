package com.microsoft.semantickernel.semanticfunctions;

import com.azure.core.exception.HttpResponseException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.TextAIService;
import com.microsoft.semantickernel.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.hooks.FunctionInvokedEvent;
import com.microsoft.semantickernel.hooks.FunctionInvokingEvent;
import com.microsoft.semantickernel.hooks.KernelHooks;
import com.microsoft.semantickernel.hooks.PromptRenderedEvent;
import com.microsoft.semantickernel.hooks.PromptRenderingEvent;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionArguments;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.services.AIServiceSelection;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class KernelFunctionFromPrompt<T> extends KernelFunction<T> {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelFunctionFromPrompt.class);

    private final PromptTemplate template;

    public KernelFunctionFromPrompt(
        PromptTemplate template,
        PromptTemplateConfig promptConfig,
        @Nullable
        Map<String, PromptExecutionSettings> executionSettings) {
        super(
            new KernelFunctionMetadata(
                getName(promptConfig),
                promptConfig.getDescription(),
                promptConfig.getKernelParametersMetadata(),
                promptConfig.getKernelReturnParameterMetadata()
            ),
            executionSettings != null ? executionSettings : promptConfig.getExecutionSettings()
        );
        this.template = template;
    }

    private static String getName(PromptTemplateConfig promptConfig) {
        if (promptConfig.getName() == null) {
            return UUID.randomUUID().toString();
        } else {
            return promptConfig.getName();
        }
    }

    public static <T> KernelFunction<T> create(
        PromptTemplateConfig promptConfig
    ) {
        return create(
            promptConfig,
            null
        );
    }

    public static <T> KernelFunction<T> create(
        PromptTemplateConfig promptConfig,
        @Nullable
        PromptTemplateFactory promptTemplateFactory
    ) {
        if (promptTemplateFactory == null) {
            promptTemplateFactory = new KernelPromptTemplateFactory();
        }

        return create(promptTemplateFactory.tryCreate(promptConfig), promptConfig);
    }


    public static <T> KernelFunction<T> create(
        PromptTemplate promptTemplate,
        PromptTemplateConfig promptConfig) {
        return new KernelFunctionFromPrompt<>(
            promptTemplate,
            promptConfig,
            null
        );
    }

    private Flux<FunctionResult<T>> invokeInternalAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable ContextVariableType<T> contextVariableType,
        @Nullable InvocationContext invocationContext) {

        InvocationContext context =
            invocationContext != null ? invocationContext : InvocationContext.builder().build();

        // must be effectively final for lambda
        KernelHooks kernelHooks = context.getKernelHooks() != null
            ? context.getKernelHooks()
            : kernel.getGlobalKernelHooks();
        assert kernelHooks != null : "getGlobalKernelHooks() should never return null";

        PromptRenderingEvent preRenderingHookResult = kernelHooks
            .executeHooks(new PromptRenderingEvent(this, arguments));

        // TOOD: put in method, add catch for classcastexception, fallback to noopconverter
        ContextVariableType<T> variableType = contextVariableType != null
            ? contextVariableType
            : context.getContextVariableTypes().getVariableTypeForClass(
                (Class<T>) this.getMetadata().getReturnParameter().getParameterType()
            );

        return this
            .template
            .renderAsync(kernel, preRenderingHookResult.getArguments(), context)
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
                        args
                    );

                AIService client =
                    aiServiceSelection != null ? aiServiceSelection.getService() : null;
                if (aiServiceSelection == null) {
                    throw new IllegalStateException(
                        "Failed to initialise aiService, could not find any TextAIService implementations");
                }

                Flux<FunctionResult<T>> result;

                // settings from prompt or use default
                PromptExecutionSettings executionSettings = aiServiceSelection.getSettings();

                if (client instanceof ChatCompletionService) {
                    result = ((ChatCompletionService) client)
                        .getChatMessageContentsAsync(
                            prompt,
                            kernel,
                            context)
                        .flatMapMany(Flux::fromIterable)
                        .concatMap(chatMessageContent -> {
                            if (chatMessageContent.getAuthorRole()
                                == AuthorRole.ASSISTANT) {

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
                                        chatMessageContent.getMetadata()
                                    )
                                );
                            } else if (chatMessageContent.getAuthorRole()
                                == AuthorRole.TOOL) {
                                String content = chatMessageContent.getContent();
                                if (content == null || content.isEmpty()) {
                                    return Flux.error(new IllegalStateException(
                                        "Tool message content is empty"));
                                }
                                Mono<FunctionResult<T>> toolResult = invokeTool(kernel, content,
                                    context);
                                return toolResult.flux();
                            }
                            return Flux.empty();
                        })
                        .map(it -> {
                            return new FunctionResult<>(
                                new ContextVariable<>(
                                    variableType,
                                    variableType.of(it.getResult()).getValue()
                                ),
                                it.getMetadata()
                            );
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
                                        value
                                    ),
                                    textContent.getMetadata()
                                )
                            );
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
                        getSkillName(),
                        getName(),
                        ex.getMessage());

                    // Common message when you attempt to send text completion
                    // requests to a chat completion model:
                    //    "logprobs, best_of and echo parameters are not
                    // available on gpt-35-turbo model"
                    if (ex instanceof HttpResponseException
                        && ((HttpResponseException) ex).getResponse().getStatusCode()
                        == 400
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

    /*
     * Given a json string, invoke the tool specified in the json string.
     * At this time, the only tool we have is 'function'.
     * The json string should be of the form:
     * {"type":"function", "function": {"name":"search-search", "parameters": {"query":"Banksy"}}}
     * where 'name' is <plugin name '-' function name>.
     */
    private Mono<FunctionResult<T>> invokeTool(
        Kernel kernel,
        String json,
        InvocationContext invocationContext) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode jsonNode = mapper.readTree(json);
            jsonNode = jsonNode.get("function");
            if (jsonNode != null) {
                return invokeFunction(kernel, jsonNode, invocationContext);
            }
        } catch (JsonProcessingException e) {
            LOGGER.error("Failed to parse json", e);
        } catch (Exception e) {
            LOGGER.error("Failed to invoke tool", e);
        }
        return Mono.empty();
    }

    /*
     * The jsonNode should represent: {"name":"search-search", "parameters": {"query":"Banksy"}}}
     */
    @SuppressWarnings({"StringSplitter", "unchecked"})
    private Mono<FunctionResult<T>> invokeFunction(
        Kernel kernel,
        JsonNode jsonNode,
        InvocationContext invocationContext
    ) {
        String name = jsonNode.get("name").asText();
        String[] parts = name.split("-");
        String pluginName = parts.length > 0 ? parts[0] : "";
        String fnName = parts.length > 1 ? parts[1] : "";
        JsonNode parameters = jsonNode.get("parameters");
        if (parameters != null) {
            try {
                KernelFunction<T> kernelFunction;
                try {
                    // unchecked cast
                    kernelFunction = (KernelFunction<T>) kernel.getPlugins()
                        .getFunction(pluginName, fnName);
                } catch (IllegalArgumentException | ClassCastException e) {
                    return Mono.error(new SKException(e.getMessage(), e));
                }

                List<KernelParameterMetadata<?>> params = kernelFunction.getMetadata()
                    .getParameters();
                Map<String, KernelParameterMetadata<?>> parameterMetaaData =
                    params.stream()
                        .collect(Collectors.toMap(KernelParameterMetadata::getName, it -> it));

                Map<String, ContextVariable<?>> variables = new HashMap<>();
                parameters.fields().forEachRemaining(entry -> {
                    String paramName = entry.getKey();
                    String paramValue = entry.getValue().asText();

                    KernelParameterMetadata<?> parameterMetadata = parameterMetaaData.get(
                        paramName);
                    if (parameterMetadata == null) {
                        // parameter in json not found in function metadata
                        // TODO: this shouldn't happen, so log it. 
                        return;
                    }

                    Class<?> parameterType = parameterMetadata.getType();
                    ContextVariable<?> contextVariable = ContextVariable.untypedOf(
                        paramValue,
                        parameterType,
                        invocationContext.getContextVariableTypes()
                    );
                    variables.put(paramName, contextVariable);
                });
                KernelFunctionArguments arguments = KernelFunctionArguments.builder()
                    .withVariables(variables)
                    .build();
                return kernelFunction.invokeAsync(kernel).withArguments(arguments);
            } catch (Exception e) {
                return Mono.error(e);
            }
        }
        return Mono.empty();
    }

    public static <T> KernelFunction<T> create(
        String promptTemplate) {
        return create(promptTemplate, null, null, null, null, null);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt specified via a prompt template.
    /// </summary>
    /// <param name="promptTemplate">Prompt template for the function, defined using the <see cref="PromptTemplateConfig.SemanticKernelTemplateFormat"/> template format.</param>
    /// <param name="executionSettings">Default execution settings to use when invoking this prompt function.</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="description">The description to use for the function.</param>
    /// <param name="templateFormat">Optional format of the template. Must be provided if a prompt template factory is provided</param>
    /// <param name="promptTemplateFactory">Optional: Prompt template factory</param>
    /// <param name="loggerFactory">Logger factory</param>
    /// <returns>A function ready to use</returns>
    @SuppressWarnings("unchecked")
    public static <T> KernelFunction<T> create(
        String promptTemplate,
        @Nullable Map<String, PromptExecutionSettings> executionSettings,
        @Nullable String functionName,
        @Nullable String description,
        @Nullable String templateFormat,
        @Nullable PromptTemplateFactory promptTemplateFactory) {

        if (templateFormat == null) {
            templateFormat = PromptTemplateConfig.SEMANTIC_KERNEL_TEMPLATE_FORMAT;
        }

        if (functionName == null) {
            functionName = UUID.randomUUID().toString();
        }

        return (KernelFunction<T>) new KernelFunctionFromPrompt.Builder<>()
            .withName(functionName)
            .withDescription(description)
            .withPromptTemplateFactory(promptTemplateFactory)
            .withTemplate(promptTemplate)
            .withTemplateFormat(templateFormat)
            .withExecutionSettings(executionSettings)
            .build();
    }

    public static <T> Builder<T> builder() {
        return new Builder<>();
    }

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
        private OutputVariable outputVariable;
        @Nullable
        private PromptTemplateFactory promptTemplateFactory;


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
            @Nullable
            Map<String, PromptExecutionSettings> executionSettings) {
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
        public FromPromptBuilder<T> withOutputVariable(@Nullable OutputVariable outputVariable) {
            this.outputVariable = outputVariable;
            return this;
        }

        @Override
        public FromPromptBuilder<T> withOutputVariable(@Nullable String description, String type) {
            return this.withOutputVariable(new OutputVariable(description, type));
        }

        @Override
        public FromPromptBuilder<T> withPromptTemplateFactory(
            @Nullable
            PromptTemplateFactory promptTemplateFactory) {
            this.promptTemplateFactory = promptTemplateFactory;
            return this;
        }

        @Override
        public KernelFunction<T> build() {

            if (template == null) {
                throw new IllegalStateException("Template must be provided");
            }

            PromptTemplateConfig config = new PromptTemplateConfig(
                name,
                template,
                templateFormat,
                description,
                inputVariables,
                outputVariable,
                executionSettings
            );

            PromptTemplate temp;
            if (promptTemplate != null) {
                temp = promptTemplate;
            } else if (promptTemplateFactory != null) {
                temp = promptTemplateFactory.tryCreate(config);
            } else {
                temp = new KernelPromptTemplateFactory().tryCreate(config);
            }

            return new KernelFunctionFromPrompt<>(temp, config, executionSettings);

        }

        public KernelFunction<T> build(PromptTemplateConfig functionModel) {

            if (promptTemplate == null) {
                throw new IllegalStateException("Template must be provided");
            }

            return new KernelFunctionFromPrompt<>(
                promptTemplate,
                functionModel,
                executionSettings
            );
        }
    }
}
