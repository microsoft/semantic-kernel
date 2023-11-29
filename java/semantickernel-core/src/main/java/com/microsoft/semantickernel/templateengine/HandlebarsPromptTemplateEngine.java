package com.microsoft.semantickernel.v1.templateengine;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Helper;
import com.github.jknack.handlebars.Options;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.blocks.Block;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;

public class HandlebarsPromptTemplateEngine implements PromptTemplateEngine {

    @Override
    public Mono<String> renderAsync(String s, SKContext skContext) {
        return null;
    }

    @Override
    public List<Block> extractBlocks(String s) {
        return null;
    }

    public Mono<String> renderAsync(String promptTemplate, Map<String, Object> variables) throws IOException {
        HandleBarsPromptTemplateHandler handler = new HandleBarsPromptTemplateHandler(promptTemplate);

        return handler.render(variables);
    }

    public static class HandleBarsPromptTemplateHandler {
        private final String template;
        private final Handlebars handlebars;
        private final ObjectMapper objectMapper;

        public HandleBarsPromptTemplateHandler(String template) {
            this.template = template;
            this.handlebars = new Handlebars();
            this.handlebars.registerHelper("message", new Helper<Object>() {
                @Override
                public Object apply(Object context, Options options) throws IOException {
                    String role = options.hash("role");

                    if (role == null || role.isEmpty()) {
                        role = ((ChatHistory.Message) context).getAuthorRoles().toString().toLowerCase();
                    }

                    if (!role.isEmpty()) {
                        return new Handlebars.SafeString(String.format("<message role=\"%s\">%s</message>", role,
                                options.fn(context)));
                    }
                    return "";
                }
            });

            this.objectMapper = new ObjectMapper();
        }

        public Mono<String> render(Map<String, Object> variables) {
            AtomicReference<String> template = new AtomicReference<>(this.template);
            variables.forEach((k, v) -> {
                try {
                    template.set(handlebars.compileInline(template.get()).apply(v));
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            });
            return Mono.just(template.get());
        }
    }

}
