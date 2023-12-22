// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.handlebars;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Locale;
import java.util.Map.Entry;
import java.util.Optional;
import java.util.Set;

import javax.annotation.Nullable;

import com.github.jknack.handlebars.Context;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.ValueResolver;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.chatcompletion.ChatMessageContent;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;

import reactor.core.publisher.Mono;

public class HandlebarsPromptTemplate implements PromptTemplate {

    @Nullable
    private PromptTemplateConfig promptTemplate;

    public HandlebarsPromptTemplate() {
        this(null);
    }

    public HandlebarsPromptTemplate(
        @Nullable PromptTemplateConfig promptTemplate) {
        this.promptTemplate = promptTemplate;
    }


    @Override
    public Mono<String> renderAsync(Kernel kernel,
        @Nullable KernelArguments arguments) {
        HandleBarsPromptTemplateHandler handler =
            new HandleBarsPromptTemplateHandler(promptTemplate.getTemplate());

        return handler.render(arguments);
    }

    private static class MessageResolver implements ValueResolver {

        @Override
        public Object resolve(Object context, String name) {
            if (context instanceof ChatMessageContent) {
                if ("role".equals(name.toLowerCase())) {
                    return ((ChatMessageContent) context).getAuthorRole().name();
                } else if ("content".equals(name.toLowerCase())) {
                    return ((ChatMessageContent) context).getContent();
                }
            }
            return UNRESOLVED;
        }

        @Override
        public Object resolve(Object context) {
            if (context instanceof ChatMessageContent) {
                return ((ChatMessageContent) context).getContent();
            }
            return UNRESOLVED;
        }

        @Override
        public Set<Entry<String, Object>> propertySet(Object context) {
            if (context instanceof ChatMessageContent) {
                HashMap<String, Object> result = new HashMap<>();
                result.put("role", ((ChatMessageContent) context).getAuthorRole().name());
                result.put("content", ((ChatMessageContent) context).getContent());
                return result.entrySet();
            }
            return new HashSet<>();
        }
    }

    private static class ContextVariableResolver implements ValueResolver {

        @Override
        public Object resolve(Object context, String name) {
            if (context instanceof KernelArguments) {
                return ((KernelArguments) context).get(name).getValue();
            }
            if (context instanceof ContextVariable) {
                return ((ContextVariable<?>) context).getValue();
            }
            return null;
        }

        @Override
        public Object resolve(Object context) {
            if (context instanceof ContextVariable) {
                return ((ContextVariable<?>) context).getValue();
            }
            return UNRESOLVED;
        }

        @Override
        public Set<Entry<String, Object>> propertySet(Object context) {
            if (context instanceof KernelArguments) {
                HashMap<String, Object> result = new HashMap<>();
                result.putAll((KernelArguments) context);
                return result.entrySet();
            } else if (context instanceof ContextVariable) {
                HashMap<String, Object> result = new HashMap<>();
                result.put("value", ((ContextVariable<?>) context).getValue());
                return result.entrySet();
            }
            return new HashSet<>();
        }
    }

    public static class HandleBarsPromptTemplateHandler {

        private final String template;
        private final Handlebars handlebars;

        public HandleBarsPromptTemplateHandler(String template) {
            this.template = template;
            this.handlebars = new Handlebars();
            this.handlebars.registerHelper(
                "message",
                (context, options) -> {
                        String role = options.hash("role");
                        String content = (String) options.fn(context);

                        if (context instanceof Optional) {
                            ChatMessageContent message = ((Optional<ChatMessageContent>) context).orElse(
                                null);
                            if (role == null || role.isEmpty()) {
                                role = message.getAuthorRole().name();
                            }
                            content = message.getContent();
                        }

                        if (role != null && !role.isEmpty()) {
                            return new Handlebars.SafeString(
                                String.format(
                                    "<message role=\"%s\">%s</message>",
                                    role.toLowerCase(Locale.ROOT), content));
                        }
                        return "";
                    }
                )

                .registerHelper(
                "each",
                    (context, options) -> {
                        if (context instanceof ChatHistory) {
                            StringBuilder sb = new StringBuilder();
                            for(ChatMessageContent message : (ChatHistory) context) {
                                sb.append(options.fn(message));
                            }
                            return new Handlebars.SafeString(sb.toString());
                        }
                        return "";
                    }
                )

                .registerHelper(
                "functions",
                    (context, options) -> {
                        StringBuilder functions = new StringBuilder("<functions>");
                        // What to do here? 
                        functions.append("</functions>");
                        
                        return functions.toString();
                    }
                )

                .registerHelper(
                "function",
                    (context, options) -> {
                        String pluginName = options.hash("pluginName");
                        String functionName = options.hash("name");
                        // What to do here?
                        return String.format(
                            "<function pluginName=\"%s\" name=\"%s\" />",
                            pluginName, functionName);
                    }
                );
                // TODO: 1.0 Add more helpers
        }


        public Mono<String> render(KernelArguments variables) {
            try {
                ArrayList<ValueResolver> resolvers = new ArrayList<>();
                resolvers.add(new MessageResolver());
                resolvers.add(new ContextVariableResolver());

                // resolvers.addAll(ValueResolver.defaultValueResolvers());

                Context context = Context
                    .newBuilder(variables)
                    .resolver(resolvers.toArray(new ValueResolver[0]))
                    .build();

                String result = handlebars.compileInline(template).apply(context);
                return Mono.just(result);
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }
}
