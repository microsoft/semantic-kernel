package com.microsoft.semantickernel.semanticfunctions;

import com.azure.core.exception.HttpResponseException;
import com.microsoft.semantickernel.AIService;
import com.microsoft.semantickernel.DefaultKernelFunction;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatCompletionService;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.StreamingContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariableType;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig.ExecutionSettingsModel;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig.VariableViewModel;
import com.microsoft.semantickernel.textcompletion.TextGenerationService;
import java.util.List;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class KernelFunctionFromPrompt extends DefaultKernelFunction {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelFunctionFromPrompt.class);

    private final PromptTemplate template;
    private final PromptTemplateConfig promptConfig;

    public KernelFunctionFromPrompt(PromptTemplate template, PromptTemplateConfig promptConfig) {
        this.template = template;
        this.promptConfig = promptConfig;
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

                AIService client = kernel.getServiceSelector()
                    .getService(TextGenerationService.class);

                if (client == null) {
                    throw new IllegalStateException("Failed to initialise aiService");
                }

                Flux<StreamingContent<T>> result;

                if (client instanceof ChatCompletionService) {
                    result = ((ChatCompletionService) client)
                        .getStreamingChatMessageContentsAsync(
                            prompt,
                            arguments.getExecutionSettings(),
                            kernel)
                        .flatMap(streamingChatMessageContent -> {
                            T value = variableType
                                .getConverter()
                                .fromPromptString(
                                    streamingChatMessageContent.innerContent.getContent());
                            return Flux.just(new StreamingContent<T>(value));
                        });
                } else if (client instanceof TextGenerationService) {
                    result = ((TextGenerationService) client)
                        .getStreamingTextContentsAsync(
                            prompt,
                            arguments.getExecutionSettings(),
                            kernel)
                        .flatMap(streamingTextContent -> {
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
        return null;
    }

    public static final class Builder implements FromPromptBuilder {

        private PromptTemplate promptTemplate;
        private String name;
        private String pluginName;
        private List<ExecutionSettingsModel> executionSettings;
        private String description;
        private List<VariableViewModel> inputVariables;
        private String template;
        private String templateFormat;
        private VariableViewModel outputVariable;


        @Override
        public FromPromptBuilder withName(String name) {
            this.name = name;
            return this;
        }

        @Override
        public FromPromptBuilder withInputParameters(List<VariableViewModel> inputVariables) {
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
            List<ExecutionSettingsModel> executionSettings) {
            this.executionSettings = executionSettings;
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
        public FromPromptBuilder withOutputVariable(VariableViewModel outputVariable) {
            this.outputVariable = outputVariable;
            return this;
        }

        @Override
        public KernelFunction build() {
            return new KernelFunctionFromPrompt(
                promptTemplate,
                new PromptTemplateConfig(
                    name,
                    template,
                    templateFormat,
                    description,
                    inputVariables,
                    outputVariable,
                    executionSettings
                )
            );
        }

        public KernelFunction build(PromptTemplateConfig functionModel) {
            return new KernelFunctionFromPrompt(
                promptTemplate,
                functionModel
            );
        }
    }
}
