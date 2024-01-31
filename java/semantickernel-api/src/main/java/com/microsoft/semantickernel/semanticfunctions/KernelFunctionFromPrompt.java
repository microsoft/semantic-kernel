package com.microsoft.semantickernel.semanticfunctions;

import com.azure.core.exception.HttpResponseException;
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
import com.microsoft.semantickernel.orchestration.DefaultKernelFunction;
import com.microsoft.semantickernel.orchestration.FunctionResult;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.DefaultKernelArguments;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.services.AIServiceSelection;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
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

public class KernelFunctionFromPrompt extends DefaultKernelFunction {

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

    public static KernelFunction create(
        PromptTemplateConfig promptConfig
    ) {
        return create(
            promptConfig,
            null
        );
    }

    public static KernelFunction create(
        PromptTemplateConfig promptConfig,
        @Nullable
        PromptTemplateFactory promptTemplateFactory
    ) {
        if (promptTemplateFactory == null) {
            promptTemplateFactory = new KernelPromptTemplateFactory();
        }

        return create(promptTemplateFactory.tryCreate(promptConfig), promptConfig);
    }


    public static KernelFunction create(
        PromptTemplate promptTemplate,
        PromptTemplateConfig promptConfig) {
        return new KernelFunctionFromPrompt(
            promptTemplate,
            promptConfig,
            null
        );
    }

    private <T> Flux<FunctionResult<T>> invokeInternalAsync(
        Kernel kernel,
        @Nullable KernelArguments argumentsIn,
        KernelHooks kernelHooks,
        ContextVariableType<T> variableType) {

        KernelArguments arguments;
        if (argumentsIn == null) {
            arguments = new DefaultKernelArguments();
        } else {
            arguments = argumentsIn;
        }

        PromptRenderingEvent preRenderingHookResult = kernelHooks
            .executeHooks(new PromptRenderingEvent(this, arguments));

        return this
            .template
            .renderAsync(kernel, preRenderingHookResult.getArguments())
            .flatMapMany(prompt -> {
                PromptRenderedEvent promptHookResult = kernelHooks
                    .executeHooks(new PromptRenderedEvent(this, arguments, prompt));
                prompt = promptHookResult.getPrompt();
                KernelArguments args = promptHookResult.getArguments();

                LOGGER.info("RENDERED PROMPT: \n{}", prompt);

                FunctionInvokingEvent updateArguments = kernelHooks
                    .executeHooks(new FunctionInvokingEvent(this, args));
                args = updateArguments.getArguments();

                AIServiceSelection aiServiceSelection = kernel
                    .getServiceSelector()
                    .trySelectAIService(
                        TextAIService.class,
                        this,
                        args
                    );

                if (aiServiceSelection == null) {
                    throw new IllegalStateException(
                        "Failed to initialise aiService, could not find any TextAIService implementations");
                }

                AIService client = aiServiceSelection.getService();
                if (client == null) {
                    throw new IllegalStateException(
                        "Failed to initialise aiService, could not find any TextAIService implementations");
                }

                Flux<FunctionResult<T>> result;

                PromptExecutionSettings executionSettings = aiServiceSelection.getSettings();

                if (client instanceof ChatCompletionService) {
                    result = ((ChatCompletionService) client)
                        .getChatMessageContentsAsync(
                            prompt,
                            executionSettings,
                            kernel,
                            kernelHooks)
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
                                Mono<FunctionResult<String>> toolResult = invokeTool(kernel,
                                    content);
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
    public <T> Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        @Nullable KernelHooks kernelHooks,
        @Nullable
        ContextVariableType<T> variableType) {
        if (variableType == null) {
            return Mono.error(new SKException(
                "Cannot invoke a prompt function without a variable return type. Ensure that there is"
                    + " a valid type converter for the return type of the prompt function."));
        }
        if (kernelHooks == null) {
            kernelHooks = kernel.getHookService();
        }
        return invokeInternalAsync(kernel, arguments, kernelHooks, variableType)
            .take(1)
            .single();
    }

    @Override
    public <T> Mono<FunctionResult<T>> invokeAsync(
        Kernel kernel,
        @Nullable
        KernelArguments arguments,
        @Nullable
        ContextVariableType<T> variableType) {
        return invokeAsync(kernel, arguments, null, variableType);
    }


    /*
     * Given a json string, invoke the tool specified in the json string.
     * At this time, the only tool we have is 'function'.
     * The json string should be of the form:
     * {"type":"function", "function": {"name":"search-search", "parameters": {"query":"Banksy"}}}
     * where 'name' is <plugin name '-' function name>.
     */
    private Mono<FunctionResult<String>> invokeTool(Kernel kernel, String json) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode jsonNode = mapper.readTree(json);
            jsonNode = jsonNode.get("function");
            if (jsonNode != null) {
                return invokeFunction(kernel, jsonNode);
            }
        } catch (Exception e) {
            LOGGER.error("Failed to parse json", e);
        }
        return Mono.empty();
    }

    /*
     * The jsonNode should represent: {"name":"search-search", "parameters": {"query":"Banksy"}}}
     */
    @SuppressWarnings("StringSplitter")
    private Mono<FunctionResult<String>> invokeFunction(Kernel kernel, JsonNode jsonNode) {
        String name = jsonNode.get("name").asText();
        String[] parts = name.split("-");
        String pluginName = parts.length > 0 ? parts[0] : "";
        String fnName = parts.length > 1 ? parts[1] : "";
        JsonNode parameters = jsonNode.get("parameters");
        if (parameters != null) {
            try {
                KernelFunction kernelFunction = kernel.getPlugins().getFunction(pluginName, fnName);

                ContextVariableType<String> variableType = ContextVariableTypes.getDefaultVariableTypeForClass(
                    String.class);
                Map<String, ContextVariable<?>> variables = new HashMap<>();
                parameters.fields().forEachRemaining(entry -> {
                    String paramName = entry.getKey();
                    String paramValue = entry.getValue().asText();
                    ContextVariable<String> contextVariable = new ContextVariable<>(variableType,
                        paramValue);
                    variables.put(paramName, contextVariable);
                });
                KernelArguments arguments = KernelArguments.builder().withVariables(variables)
                    .build();
                return kernelFunction.invokeAsync(kernel, arguments, variableType);
            } catch (Exception e) {
                return Mono.error(e);
            }
        }
        return Mono.empty();
    }

    public static KernelFunction create(
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
    public static KernelFunction create(
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

        return new KernelFunctionFromPrompt.Builder()
            .withName(functionName)
            .withDescription(description)
            .withPromptTemplateFactory(promptTemplateFactory)
            .withTemplate(promptTemplate)
            .withTemplateFormat(templateFormat)
            .withExecutionSettings(executionSettings)
            .build();
    }

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder implements FromPromptBuilder {

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
        public FromPromptBuilder withName(@Nullable String name) {
            this.name = name;
            return this;
        }

        @Override
        public FromPromptBuilder withInputParameters(@Nullable List<InputVariable> inputVariables) {
            if (inputVariables != null) {
                this.inputVariables = new ArrayList<>(inputVariables);
            } else {
                this.inputVariables = null;
            }
            return this;
        }

        @Override
        public FromPromptBuilder withPromptTemplate(@Nullable PromptTemplate promptTemplate) {
            this.promptTemplate = promptTemplate;
            return this;
        }

        @Override
        public FromPromptBuilder withExecutionSettings(
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
        public FromPromptBuilder withDefaultExecutionSettings(
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
        public FromPromptBuilder withDescription(@Nullable String description) {
            this.description = description;
            return this;
        }

        @Override
        public FromPromptBuilder withTemplate(@Nullable String template) {
            this.template = template;
            return this;
        }


        @Override
        public FromPromptBuilder withTemplateFormat(String templateFormat) {
            this.templateFormat = templateFormat;
            return this;
        }

        @Override
        public FromPromptBuilder withOutputVariable(@Nullable OutputVariable outputVariable) {
            this.outputVariable = outputVariable;
            return this;
        }

        @Override
        public FromPromptBuilder withPromptTemplateFactory(
            @Nullable
            PromptTemplateFactory promptTemplateFactory) {
            this.promptTemplateFactory = promptTemplateFactory;
            return this;
        }

        @Override
        public KernelFunction build() {

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

            return new KernelFunctionFromPrompt(temp, config, executionSettings);

        }

        public KernelFunction build(PromptTemplateConfig functionModel) {

            if (promptTemplate == null) {
                throw new IllegalStateException("Template must be provided");
            }

            return new KernelFunctionFromPrompt(
                promptTemplate,
                functionModel,
                executionSettings
            );
        }
    }
}
