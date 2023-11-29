package com.microsoft.semantickernel.v1.templateengine;

import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Template;
import com.github.jknack.handlebars.io.ClassPathTemplateLoader;
import com.github.jknack.handlebars.io.TemplateLoader;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.skilldefinition.ParameterView;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.util.List;
import java.util.Map;

public class HandlebarsPromptTemplate implements PromptTemplate {
    private String promptTemplate;
    private HandlebarsPromptTemplateEngine templateEngine;

    public HandlebarsPromptTemplate(String promptTemplate, PromptTemplateEngine templateEngine) {
        this.promptTemplate = promptTemplate;
        this.templateEngine = (HandlebarsPromptTemplateEngine) templateEngine;
    }

    @Override
    public List<ParameterView> getParameters() {
        return null;
    }

    @Override
    public Mono<String> renderAsync(SKContext skContext) {
        return null;
    }

    public Mono<String> renderAsync(Map<String, Object> variables) throws IOException {
        return templateEngine.renderAsync(this.promptTemplate, variables);
    }
}
