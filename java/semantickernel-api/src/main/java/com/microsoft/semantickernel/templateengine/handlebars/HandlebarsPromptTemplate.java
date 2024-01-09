// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.handlebars;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
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
import com.microsoft.semantickernel.orchestration.KernelFunction;
import com.microsoft.semantickernel.orchestration.contextvariables.ContextVariable;
import com.microsoft.semantickernel.orchestration.contextvariables.KernelArguments;
import com.microsoft.semantickernel.plugin.KernelParameterMetadata;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.plugin.KernelPluginCollection;
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
            new HandleBarsPromptTemplateHandler(kernel, promptTemplate.getTemplate());

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

    private static class KernelPluginResolver implements ValueResolver {

        @Override
        public Object resolve(Object context, String name) {
            if (context instanceof KernelPluginCollection) {    
                return context;
            }
            if (context instanceof KernelFunction) {
                KernelFunction function = (KernelFunction) context;
                if ("pluginname".equals(name.toLowerCase())) {
                    return function.getSkillName();
                } else if ("name".equals(name.toLowerCase())) {
                    return function.getName();
                }
            }
            return UNRESOLVED;
        }

        @Override
        public Object resolve(Object context) {
            if (context instanceof KernelPluginCollection) {    
                return ((KernelPluginCollection) context).iterator();
            }
            return UNRESOLVED;
        }

        @Override
        public Set<Entry<String, Object>> propertySet(Object context) {
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
            return UNRESOLVED;
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

        private final Kernel kernel;
        private final String template;
        private final Handlebars handlebars;

        public HandleBarsPromptTemplateHandler(Kernel kernel, String template) {
            this.kernel = kernel;
            this.template = template;
            this.handlebars = new Handlebars();
            this.handlebars.registerHelper(
                "message",
                (context, options) -> {
                        String role = options.hash("role");
                        String content = (String) options.fn(context);

                        if (context instanceof Optional) {
                            ChatMessageContent message = ((Optional<ChatMessageContent>) context).orElse(null);
                            if (message != null) {
                                if (role == null || role.isEmpty()) {
                                    role = message.getAuthorRole().name();
                                }
                                content = message.getContent();
                            }
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
                            StringBuilder sb = new StringBuilder("<messages>");
                            for(ChatMessageContent message : (ChatHistory) context) {
                                sb.append(options.fn(message));
                            }
                            sb.append("</messages>");
                            return new Handlebars.SafeString(sb.toString());
                        }
                        if (context instanceof KernelPluginCollection) {
                            StringBuilder sb = new StringBuilder();
                            Iterator<KernelPlugin> plugins = ((KernelPluginCollection) context).iterator();
                            while (plugins.hasNext()) {
                                KernelPlugin plugin = plugins.next();
                                Iterator<KernelFunction> functions = plugin.iterator();
                                while (functions.hasNext()) {
                                    KernelFunction function = functions.next();
                                    sb.append(options.fn(function));
                                }
                            }
                            return new Handlebars.SafeString(sb.toString());
                        }
                        return "";
                    }
                )

                .registerHelper(
                "functions",
                    (context, options) -> {
                        StringBuilder sb = new StringBuilder("<functions>");
                        KernelPluginCollection plugins = kernel.getPlugins();
                        sb.append(options.fn(plugins));
                        sb.append("</functions>");
                        
                        return new Handlebars.SafeString(sb.toString());
                    }
                )

                .registerHelper(
                "function",
                    (context, options) -> {
                        KernelFunction function = (KernelFunction) context;
                        String pluginName = function.getSkillName();
                        String functionName = function.getName();
                        String description = function.getDescription();
                        StringBuilder sb = new StringBuilder(
                            String.format(
                                "<function pluginName=\"%s\" name=\"%s\" description=\"%s\">",
                                pluginName, functionName, description));
                        List<KernelParameterMetadata> parameters = function.getMetadata().getParameters();
                        parameters.forEach(p -> {
                            sb.append(String.format(
                                "<parameter name=\"%s\" description=\"%s\" defaultValue=\"%s\" isRequired=\"%s\" type=\"%s\"/>",
                                p.getName(), p.getDescription(), p.getDefaultValue(), p.isRequired(), p.getType()));
                        });
                        sb.append("</function>");
                        return new Handlebars.SafeString(sb.toString());
                    }
                );
                // TODO: 1.0 Add more helpers
        }


        public Mono<String> render(KernelArguments variables) {
            try {
                ArrayList<ValueResolver> resolvers = new ArrayList<>();
                resolvers.add(new MessageResolver());
                resolvers.add(new KernelPluginResolver());
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
