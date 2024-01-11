package com.microsoft.semantickernel.semanticfunctions;

import com.azure.core.exception.HttpResponseException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.TextAIService;
import com.microsoft.semantickernel.chatcompletion.AuthorRole;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.DefaultKernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.KernelFunctionMetadata;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import com.microsoft.semantickernel.orchestration.StreamingContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableTypes;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class KernelFunctionFromPrompt extends DefaultKernelFunction {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelFunctionFromPrompt.class);

    private final PromptTemplate template;

    public KernelFunctionFromPrompt(PromptTemplate template, PromptTemplateConfig promptConfig) {
        super(
            new KernelFunctionMetadata(
                promptConfig.getName(),
                promptConfig.getDescription(),
                promptConfig.getKernelParametersMetadata(),
                promptConfig.getKernelReturnParameterMetadata()
            ),
            promptConfig.getExecutionSettings()
        );
        this.template = template;
    }

    @Override
    public <T> Flux<StreamingContent<T>> invokeStreamingAsync(
        Kernel kernel,
        @Nullable KernelArguments arguments,
        ContextVariableType<T> variableType) {
        return this
            .template
            .renderAsync(kernel, arguments)
            .flatMapMany(prompt -> {
                LOGGER.info("RENDERED PROMPT: \n{}", prompt);

                AIService client = kernel
                    .getServiceSelector()
                    .getService(TextAIService.class);

                if (client == null) {
                    throw new IllegalStateException("Failed to initialise aiService, could not find any TextAIService implementations");
                }

                Flux<StreamingContent<T>> result;

                PromptExecutionSettings executionSettings;
                if (arguments != null) {
                    executionSettings = arguments.getExecutionSettings();
                } else {
                    executionSettings = null;
                }

                if (client instanceof ChatCompletionService) {
                    result = ((ChatCompletionService) client)
                        .getStreamingChatMessageContentsAsync(
                            prompt,
                            executionSettings,
                            kernel)
                        .concatMap(streamingChatMessageContent -> {
                            if (streamingChatMessageContent.getRole() == AuthorRole.ASSISTANT) {
                                T value = variableType
                                    .getConverter()
                                    .fromPromptString(
                                        streamingChatMessageContent.getContent());
                                return Flux.just(new StreamingContent<>(value));
                            } else if (streamingChatMessageContent.getRole() == AuthorRole.TOOL) {
                                Mono<ContextVariable<String>> toolResult = invokeTool(kernel,
                                    streamingChatMessageContent.getContent());
                                return toolResult.flatMapMany(contextVariable -> {
                                    T value = variableType
                                        .getConverter()
                                        .fromPromptString(
                                            contextVariable.getValue());
                                    return Flux.just(new StreamingContent<>(value));
                                });
                            }
                            return Flux.empty();
                        });
                    return result;

                } else if (client instanceof TextGenerationService) {
                    result = ((TextGenerationService) client)
                        .getStreamingTextContentsAsync(
                            prompt,
                            executionSettings,
                            kernel)
                        .concatMap(streamingTextContent -> {
                            T value = variableType.getConverter().fromPromptString(
                                streamingTextContent.innerContent.getValue());
                            return Flux.just(new StreamingContent<>(value));
                        });
                } else {
                    return Flux.error(new IllegalStateException("Unknown service type"));
                }
                return result;
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
                        && ex.getMessage()
                        .contains("parameters are not available" + " on")) {
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
    public <T> Mono<ContextVariable<T>> invokeAsync(Kernel kernel,
        @Nullable KernelArguments arguments, ContextVariableType<T> variableType) {
        return invokeStreamingAsync(kernel, arguments, variableType)
            .collectList()
            .map(streamingContents -> {
                StringBuilder result = streamingContents
                    .stream()
                    .reduce(
                        new StringBuilder(),
                        (sb, streamingContent) -> sb.append(streamingContent.innerContent),
                        StringBuilder::append);
                T x = variableType.getConverter().fromPromptString(result.toString());
                return new ContextVariable<>(variableType, x);
            });
    }

    /*
     * Given a json string, invoke the tool specified in the json string.
     * At this time, the only tool we have is 'function'.
     * The json string should be of the form:
     * {"type":"function", "function": {"name":"search-search", "parameters": {"query":"Banksy"}}}
     * where 'name' is <plugin name '-' function name>.
     */
    private Mono<ContextVariable<String>> invokeTool(Kernel kernel, String json) {
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
    private Mono<ContextVariable<String>> invokeFunction(Kernel kernel, JsonNode jsonNode) {
        String name = jsonNode.get("name").asText();
        String[] parts = name.split("-");
        String pluginName = parts.length > 0 ? parts[0] : "";
        String fnName = parts.length > 1 ? parts[1] : "";
        JsonNode parameters = jsonNode.get("parameters");
        if (parameters != null) {
            KernelFunction kernelFunction = kernel.getPlugins().getFunction(pluginName, fnName);
            if (kernelFunction == null) {
                return Mono.empty();
            }
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
            KernelArguments arguments = KernelArguments.builder().withVariables(variables).build();
            return kernelFunction.invokeAsync(kernel, arguments, variableType);
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

        return new KernelFunctionFromPrompt.Builder()
            .withName(functionName)
            .withDescription(description)
            .withPromptTemplateFactory(promptTemplateFactory)
            .withTemplate(promptTemplate)
            .withTemplateFormat(templateFormat)
            .withExecutionSettings(executionSettings)
            .build();
    }

    public static final class Builder implements FromPromptBuilder {

        private PromptTemplate promptTemplate;
        private String name;
        private String pluginName;
        private Map<String, PromptExecutionSettings> executionSettings;
        private String description;
        private List<InputVariable> inputVariables;
        private String template;
        private String templateFormat;
        private OutputVariable outputVariable;
        private PromptTemplateFactory promptTemplateFactory;


        @Override
        public FromPromptBuilder withName(String name) {
            this.name = name;
            return this;
        }

        @Override
        public FromPromptBuilder withInputParameters(List<InputVariable> inputVariables) {
            this.inputVariables = inputVariables;
            return this;
        }

        @Override
        public FromPromptBuilder withPromptTemplate(PromptTemplate promptTemplate) {
            this.promptTemplate = promptTemplate;
            return this;
        }

        @Override
        public FromPromptBuilder withPluginName(String name) {
            this.pluginName = name;
            return this;
        }

        @Override
        public FromPromptBuilder withExecutionSettings(
            Map<String, PromptExecutionSettings> executionSettings) {
            this.executionSettings = executionSettings;
            return this;
        }

        @Override
        public FromPromptBuilder withDefaultExecutionSettings(
            PromptExecutionSettings executionSettings) {
            if (this.executionSettings == null) {
                this.executionSettings = new HashMap<>();
            }
            this.executionSettings.put("default", executionSettings);
            return this;
        }

        @Override
        public FromPromptBuilder withDescription(String description) {
            this.description = description;
            return this;
        }

        @Override
        public FromPromptBuilder withTemplate(String template) {
            this.template = template;
            return this;
        }


        @Override
        public FromPromptBuilder withTemplateFormat(String templateFormat) {
            this.templateFormat = templateFormat;
            return this;
        }

        @Override
        public FromPromptBuilder withOutputVariable(OutputVariable outputVariable) {
            this.outputVariable = outputVariable;
            return this;
        }

        @Override
        public FromPromptBuilder withPromptTemplateFactory(
            PromptTemplateFactory promptTemplateFactory) {
            this.promptTemplateFactory = promptTemplateFactory;
            return this;
        }

        @Override
        public KernelFunction build() {
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

            return new KernelFunctionFromPrompt(temp, config);

        }

        public KernelFunction build(PromptTemplateConfig functionModel) {
            return new KernelFunctionFromPrompt(
                promptTemplate,
                functionModel
            );
        }
    }
}
