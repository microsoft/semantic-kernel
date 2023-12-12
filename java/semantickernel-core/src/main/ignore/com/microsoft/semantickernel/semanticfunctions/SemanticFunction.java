// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

/**
 * @since 1.0.0
 */
/*
public class SemanticFunction extends DefaultSemanticKernelFunction {

    private static final Logger LOGGER = LoggerFactory.getLogger(SemanticFunction.class);
    private String name;
    private String pluginName;
    private String description;
    private List<PromptTemplateConfig.ExecutionSettingsModel> executionSettings;
    private List<PromptTemplateConfig.VariableViewModel> inputParameters;
    private PromptTemplate promptTemplate;

    // TODO: This should not be in core.
    public SemanticFunction(
        String name,
        String pluginName,
        String description,
        List<PromptTemplateConfig.ExecutionSettingsModel> executionSettings,
        PromptTemplate promptTemplate,
        List<PromptTemplateConfig.VariableViewModel> inputParameters) {
        super(Collections.emptyList(), name, name, description, null);
        this.name = name;
        this.pluginName = pluginName;
        this.description = description;
        this.executionSettings = executionSettings;
        this.promptTemplate = promptTemplate;
        this.inputParameters = inputParameters;
    }

    public static SemanticFunction fromYaml(Path filePath) throws IOException {
        return fromYaml(filePath.toAbsolutePath().toString());
    }

    public static SemanticFunction fromYaml(String filePath) throws IOException {
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        InputStream inputStream =
            SemanticFunction.class.getClassLoader().getResourceAsStream(filePath);

        PromptTemplateConfig functionModel =
            mapper.readValue(inputStream, PromptTemplateConfig.class);

        return new Builder()
            .withName(functionModel.getName())
            .withInputParameters(functionModel.getInputVariables())
            .withPromptTemplate(
                new HandlebarsPromptTemplate(
                    functionModel.getTemplate(), new HandlebarsPromptTemplateEngine()))
            .withPluginName(functionModel.getName()) // TODO: 1.0 add plugin name
            .withExecutionSettings(functionModel.getExecutionSettings())
            .withDescription(functionModel.getDescription())
            .build();
    }

    @Override
    public Mono<FunctionResult> invokeAsync(
        Kernel kernel, ContextVariables input, boolean streaming) {
        TextCompletion client = kernel.getService(null, TextCompletion.class);
        if (client == null) {
            throw new IllegalStateException("Failed to initialise aiService");
        }

        // TODO: 1.0 check model pattern Id to select execution settings
        PromptTemplateConfig.ExecutionSettingsModel executionSettingsModel =
            this.executionSettings.get(0);

        // TODO: 1.0 fix settings
        CompletionRequestSettings requestSettings =
            new CompletionRequestSettings(
                Double.valueOf(executionSettingsModel.getTemperature()), 0, 0, 0, 1000);

        return this.promptTemplate
            .renderAsync(input)
            .flatMap(
                prompt ->
                    performCompletionRequest(
                        client, requestSettings, prompt, streaming))
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

    private Mono<FunctionResult> performCompletionRequest(
        TextCompletion client,
        CompletionRequestSettings requestSettings,
        String prompt,
        boolean streaming) {

        LOGGER.info("RENDERED PROMPT: \n{}", prompt);

        if (streaming) {
            Flux<String> completionStream = client.completeStreamAsync(prompt, requestSettings);

            return Mono.just(
                new SemanticFunctionResult(
                    pluginName,
                    name,
                    completionStream.reduce(String::concat),
                    completionStream));
        } else {
            Mono<String> completion =
                client.completeAsync(prompt, requestSettings)
                    .map(list -> list.isEmpty() ? null : list.get(0));

            return Mono.just(new SemanticFunctionResult(pluginName, name, completion));
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

    @Override
    public void registerOnKernel(Kernel kernel) {
    }

    public static class Builder implements Buildable {

        private String name;
        private String pluginName;
        private String description;
        private List<PromptTemplateConfig.ExecutionSettingsModel> executionSettings;
        private PromptTemplate promptTemplate;
        private List<PromptTemplateConfig.VariableViewModel> inputParameters;

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
            List<PromptTemplateConfig.ExecutionSettingsModel> executionSettings) {
            this.executionSettings = executionSettings;
            return this;
        }

        public Builder withPromptTemplate(PromptTemplate promptTemplate) {
            this.promptTemplate = promptTemplate;
            return this;
        }

        public Builder withInputParameters(
            List<PromptTemplateConfig.VariableViewModel> inputParameters) {
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
*/