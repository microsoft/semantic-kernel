// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

/*
/// <summary>
/// Prompt template.
/// </summary>
public class DefaultPromptTemplate implements PromptTemplate {
    private final String promptTemplate;
    private final PromptConfig config;
    private final PromptTemplateEngine templateEngine;

    public DefaultPromptTemplate(
            String promptTemplate,
            PromptConfig config,
            PromptTemplateEngine templateEngine) {
        this.promptTemplate = promptTemplate;
        this.config = config;
        this.templateEngine = templateEngine;
    }

    @Override
    public List<ParameterView> getParameters() {
        // Parameters from config.json
        List<ParameterView> result =
                this.config.getInput().getParameters().stream()
                        .filter(Objects::nonNull)
                        .map(
                                p ->
                                        new ParameterView(
                                                p.getName(),
                                                p.getDescription(),
                                                p.getDefaultValue()))
                        .collect(Collectors.toList());

        List<String> seen =
                result.stream().map(ParameterView::getName).collect(Collectors.toList());

        List<VarBlock> listFromTemplate =
                templateEngine.extractBlocks(this.promptTemplate).stream()
                        .filter(Objects::nonNull)
                        .filter(x -> x.getType() == BlockTypes.Variable)
                        .map(x -> (VarBlock) x)
                        .collect(Collectors.toList());

        List<ParameterView> newParams =
                listFromTemplate.stream()
                        .filter(x -> !seen.contains(x.getName()))
                        .map(x -> new ParameterView(x.getName()))
                        .collect(Collectors.toList());

        return Stream.concat(result.stream(), newParams.stream()).collect(Collectors.toList());
    }

    @Override
    public Mono<String> renderAsync(SKContext executionContext) {
        return templateEngine.renderAsync(this.promptTemplate, executionContext);
    }

    @Override
    public Mono<String> renderAsync(ContextVariables variables) {
        return null;
    }

    public static final class Builder implements PromptTemplate.Builder {
        @Nullable private String promptTemplate = null;
        @Nullable private PromptConfig config = null;
        @Nullable private PromptTemplateEngine promptTemplateEngine = null;

        @Override
        public PromptTemplate.Builder withPromptTemplate(String promptTemplate) {
            this.promptTemplate = promptTemplate;
            return this;
        }

        @Override
        public PromptTemplate.Builder withPromptTemplateConfig(PromptConfig config) {
            this.config = config;
            return this;
        }

        @Override
        public PromptTemplate.Builder withPromptTemplateEngine(
                PromptTemplateEngine promptTemplateEngine) {
            this.promptTemplateEngine = promptTemplateEngine;
            return this;
        }

        @Override
        public PromptTemplate build() {
            if (promptTemplate == null || config == null || promptTemplateEngine == null) {
                throw new IllegalStateException(
                        "PromptTemplate, PromptTemplateConfig and promptTemplateEngine must be"
                                + " set");
            }
            return new DefaultPromptTemplate(promptTemplate, config, promptTemplateEngine);
        }
    }
}


 */