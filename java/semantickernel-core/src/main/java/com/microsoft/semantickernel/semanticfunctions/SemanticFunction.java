// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.azure.core.exception.HttpResponseException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.functions.SemanticFunctionResult;
import com.microsoft.semantickernel.orchestration.*;
import com.microsoft.semantickernel.skilldefinition.FunctionView;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplate;
import com.microsoft.semantickernel.templateengine.handlebars.HandlebarsPromptTemplateEngine;
import com.microsoft.semantickernel.textcompletion.CompletionRequestSettings;
import com.microsoft.semantickernel.textcompletion.TextCompletion;
import java.io.IOException;
import java.io.InputStream;
import java.util.Collections;
import java.util.List;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

public class SemanticFunction extends DefaultSemanticSKFunction {

    private static final Logger LOGGER = LoggerFactory.getLogger(DefaultCompletionSKFunction.class);
    private String name;
    private String pluginName;
    private String description;
    private List<SemanticFunctionModel.ExecutionSettingsModel> executionSettings;
    private List<SemanticFunctionModel.VariableViewModel> inputParameters;
    private SemanticAsyncTask<SemanticFunctionResult> function;
    private HandlebarsPromptTemplate promptTemplate;
    @Nullable private DefaultTextCompletionSupplier aiService;

    public SemanticFunction(
            String name,
            String pluginName,
            String description,
            List<SemanticFunctionModel.ExecutionSettingsModel> executionSettings,
            PromptTemplate promptTemplate,
            List<SemanticFunctionModel.VariableViewModel> inputParameters) {
        super(Collections.emptyList(), name, name, description, null);
        this.name = name;
        this.pluginName = pluginName;
        this.description = description;
        this.executionSettings = executionSettings;
        this.promptTemplate = (HandlebarsPromptTemplate) promptTemplate;
        this.inputParameters = inputParameters;
    }

    public static SemanticFunction fromYaml(String filePath) throws IOException {
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        InputStream inputStream =
                SemanticFunction.class.getClassLoader().getResourceAsStream(filePath);

        SemanticFunctionModel functionModel =
                mapper.readValue(inputStream, SemanticFunctionModel.class);

        return new Builder()
                .withName(functionModel.getName())
                .withInputParameters(functionModel.getInputVariables())
                .withPromptTemplate(
                        new HandlebarsPromptTemplate(
                                functionModel.getTemplate(), new HandlebarsPromptTemplateEngine()))
                .withPluginName(functionModel.getName())
                .withExecutionSettings(functionModel.getExecutionSettings())
                .withDescription(functionModel.getDescription())
                .build();
    }

    public Mono<SemanticFunctionResult> invokeAsync(ContextVariables variables) throws IOException {

        if (function == null) {
            throw new FunctionNotRegisteredException(
                    FunctionNotRegisteredException.ErrorCodes.FUNCTION_NOT_REGISTERED,
                    this.getName());
        }

        if (this.aiService.get() == null) {
            throw new IllegalStateException("Failed to initialise aiService");
        }

        SemanticFunctionModel.ExecutionSettingsModel executionSettingsModel =
                this.executionSettings.get(0);

        // TODO: 1.0 fix settings
        CompletionRequestSettings finalSettings = new CompletionRequestSettings(0.9, 0, 0, 0, 1000);

        return function.run(this.aiService.get(), finalSettings, variables);
    }

    @Override
    public void registerOnKernel(Kernel kernel) {
        this.function =
                (TextCompletion client,
                        CompletionRequestSettings requestSettings,
                        ContextVariables input) -> {
                    return promptTemplate
                            .renderAsync(input)
                            .flatMap(
                                    prompt ->
                                            performCompletionRequest(
                                                    client, requestSettings, prompt))
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
                                                && ((HttpResponseException) ex)
                                                                .getResponse()
                                                                .getStatusCode()
                                                        == 400
                                                && ex.getMessage()
                                                        .contains(
                                                                "parameters are not available"
                                                                        + " on")) {
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
                };

        this.setSkillsSupplier(kernel::getSkills);
        this.aiService = () -> kernel.getService(null, TextCompletion.class);
    }

    private static Mono<SemanticFunctionResult> performCompletionRequest(
            TextCompletion client, CompletionRequestSettings requestSettings, String prompt) {

        LOGGER.info("RENDERED PROMPT: \n{}", prompt);

        switch (client.defaultCompletionType()) {
            case NON_STREAMING:
                return client.completeAsync(prompt, requestSettings)
                        .single()
                        .map(completion -> new SemanticFunctionResult(completion.get(0)));

            case STREAMING:
            default:
                return client.completeStreamAsync(prompt, requestSettings)
                        .filter(completion -> !completion.isEmpty())
                        .take(1)
                        .single()
                        .map(SemanticFunctionResult::new);
        }
    }

    @Nullable
    @Override
    public FunctionView describe() {
        return null;
    }

    @Override
    protected Mono<SKContext> invokeAsyncInternal(SKContext context, @Nullable Object settings) {
        return null;
    }

    public static class Builder implements Buildable {
        private String name;
        private String pluginName;
        private String description;
        private List<SemanticFunctionModel.ExecutionSettingsModel> executionSettings;
        private PromptTemplate promptTemplate;
        private List<SemanticFunctionModel.VariableViewModel> inputParameters;

        public Builder withName(String name) {
            this.name = name;
            return this;
        }

        public Builder withPluginName(String pluginName) {
            this.pluginName = pluginName;
            return this;
        }

        public Builder withDescription(String description) {
            this.description = description;
            return this;
        }

        public Builder withExecutionSettings(
                List<SemanticFunctionModel.ExecutionSettingsModel> executionSettings) {
            this.executionSettings = executionSettings;
            return this;
        }

        public Builder withPromptTemplate(PromptTemplate promptTemplate) {
            this.promptTemplate = promptTemplate;
            return this;
        }

        public Builder withInputParameters(
                List<SemanticFunctionModel.VariableViewModel> inputParameters) {
            this.inputParameters = inputParameters;
            return this;
        }

        public SemanticFunction build() {
            return new SemanticFunction(
                    name,
                    pluginName,
                    description,
                    executionSettings,
                    promptTemplate,
                    inputParameters);
        }
    }
}
