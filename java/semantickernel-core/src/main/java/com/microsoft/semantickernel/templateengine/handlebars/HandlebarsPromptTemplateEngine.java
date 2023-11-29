// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.handlebars;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Helper;
import com.github.jknack.handlebars.Options;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.orchestration.ContextVariables;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.blocks.Block;
import java.io.IOException;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import reactor.core.publisher.Mono;

public class HandlebarsPromptTemplateEngine implements PromptTemplateEngine {

    @Override
    public Mono<String> renderAsync(String s, SKContext skContext) {
        throw new RuntimeException("SKContext not supported");
    }

    @Override
    public List<Block> extractBlocks(String s) {
        return null;
    }

    @Override
    public Mono<String> renderAsync(String promptTemplate, ContextVariables variables) {
        HandleBarsPromptTemplateHandler handler =
                new HandleBarsPromptTemplateHandler(promptTemplate);

        return handler.render(variables);
    }

    public static class HandleBarsPromptTemplateHandler {
        private final String template;
        private final Handlebars handlebars;
        private final ObjectMapper objectMapper;

        public HandleBarsPromptTemplateHandler(String template) {
            this.template = template;
            this.handlebars = new Handlebars();
            this.handlebars.registerHelper(
                    "message",
                    new Helper<Object>() {
                        @Override
                        public Object apply(Object context, Options options) throws IOException {
                            String role = options.hash("role");

                            if (role == null || role.isEmpty()) {
                                role =
                                        ((ChatHistory.Message) context)
                                                .getAuthorRoles()
                                                .toString()
                                                .toLowerCase();
                            }

                            if (!role.isEmpty()) {
                                return new Handlebars.SafeString(
                                        String.format(
                                                "<message role=\"%s\">%s</message>",
                                                role, options.fn(context)));
                            }
                            return "";
                        }
                    });

            this.objectMapper = new ObjectMapper();
        }

        public Mono<String> render(ContextVariables variables) {
            AtomicReference<String> template = new AtomicReference<>(this.template);

            variables
                    .asMap()
                    .forEach(
                            (k, v) -> {
                                try {
                                    // TODO: 1.0 fix
                                    if (k.equals("messages")) {
                                        template.set(
                                                handlebars.compileInline(template.get()).apply(v));
                                    }
                                } catch (IOException e) {
                                    throw new RuntimeException(e);
                                }
                            });

            return Mono.just(template.get());
        }
    }
}
