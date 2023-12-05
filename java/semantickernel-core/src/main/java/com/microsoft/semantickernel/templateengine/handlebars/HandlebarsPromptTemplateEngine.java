// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.handlebars;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.jknack.handlebars.Context;
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
import java.util.Optional;
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

        public HandleBarsPromptTemplateHandler(String template) {
            this.template = template;
            this.handlebars = new Handlebars();
            this.handlebars.registerHelper(
                    "message",
                    new Helper<Object>() {
                        @Override
                        public Object apply(Object context, Options options) throws IOException {
                            String role = options.hash("role");
                            String content = (String) options.fn(context);

                            // when message is inside a loop Context is Optional<ChatHistory.Message>
                            // when message is not inside a loop Context is the UnmodifiableMap<String, Object> with all the variables
                            if (context instanceof Optional) {
                                ChatHistory.Message message = ((Optional<ChatHistory.Message>) context).orElse(null);
                                if (role == null || role.isEmpty()) {
                                    role = message.getAuthorRoles()
                                                    .toString()
                                                    .toLowerCase();
                                }
                                content = message.getContent();
                            }

                            if (role != null && !role.isEmpty()) {
                                return new Handlebars.SafeString(
                                        String.format(
                                                "<message role=\"%s\">%s</message>",
                                                role, content));
                            }
                            return "";
                        }
                    });

            // TODO: 1.0 Add more helpers
        }

        public Mono<String> render(ContextVariables variables) {
            try {
                String result = handlebars.compileInline(template).apply(variables.asMap());
                return Mono.just(result);
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }
}
