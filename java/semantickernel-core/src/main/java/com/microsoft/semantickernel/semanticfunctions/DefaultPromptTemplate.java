// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.blocks.BlockTypes;
import com.microsoft.semantickernel.templateengine.blocks.VarBlock;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/// <summary>
/// Prompt template.
/// </summary>
public class DefaultPromptTemplate implements PromptTemplate {
    private final String promptTemplate;
    private final PromptTemplateConfig config;
    private final PromptTemplateEngine templateEngine;

    public DefaultPromptTemplate(
            String promptTemplate,
            PromptTemplateConfig config,
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

    public static final class Builder extends PromptTemplate.Builder {
        @Nullable private String promptTemplate = null;
        @Nullable private PromptTemplateConfig config = null;

        @Override
        public PromptTemplate build(PromptTemplateEngine promptTemplateEngine) {
            if (promptTemplate == null || config == null)
                throw new IllegalStateException(
                        "PromptTemplate and PromptTemplateConfig must be set");
            return new DefaultPromptTemplate(promptTemplate, config, promptTemplateEngine);
        }

        @Override
        public Builder withPromptTemplate(String promptTemplate) {
            this.promptTemplate = promptTemplate;
            return this;
        }

        @Override
        public Builder withPromptTemplateConfig(PromptTemplateConfig config) {
            this.config = config;
            return this;
        }
    }
}
