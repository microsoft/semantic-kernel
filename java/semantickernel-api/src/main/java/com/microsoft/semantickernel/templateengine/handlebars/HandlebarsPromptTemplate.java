// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.handlebars;

import com.github.jknack.handlebars.Context;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Options;
import com.github.jknack.handlebars.ValueResolver;
import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.exceptions.SKException;
import com.microsoft.semantickernel.orchestration.InvocationContext;
import com.microsoft.semantickernel.plugin.KernelPlugin;
import com.microsoft.semantickernel.semanticfunctions.KernelFunction;
import com.microsoft.semantickernel.semanticfunctions.KernelFunctionArguments;
import com.microsoft.semantickernel.semanticfunctions.KernelParameterMetadata;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.services.chatcompletion.ChatHistory;
import com.microsoft.semantickernel.services.chatcompletion.ChatMessageContent;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Locale;
import java.util.Map.Entry;
import java.util.Optional;
import java.util.Set;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import reactor.core.publisher.Mono;

/**
 * A prompt template that uses the Handlebars template engine to render prompts.
 */
public class HandlebarsPromptTemplate implements PromptTemplate {

    private final PromptTemplateConfig promptTemplate;

    /**
     * Initializes a new instance of the {@link HandlebarsPromptTemplate} class.
     *
     * @param promptTemplate The prompt template configuration.
     */
    public HandlebarsPromptTemplate(
        @Nonnull PromptTemplateConfig promptTemplate) {
        this.promptTemplate = new PromptTemplateConfig(promptTemplate);
    }

    @Override
    public Mono<String> renderAsync(
        Kernel kernel,
        @Nullable KernelFunctionArguments arguments,
        @Nullable InvocationContext context) {
        String template = promptTemplate.getTemplate();
        if (template == null) {
            return Mono.error(new SKException(
                String.format("No prompt template was provided for the prompt %s.",
                    promptTemplate.getName())));
        }
        HandleBarsPromptTemplateHandler handler = new HandleBarsPromptTemplateHandler(kernel,
            template);

        if (arguments == null) {
            arguments = new KernelFunctionArguments();
        }
        return handler.render(arguments);
    }

    private static class MessageResolver implements ValueResolver {

        @Override
        @SuppressWarnings("NullAway")
        public Object resolve(Object context, String name) {
            if (context instanceof ChatMessageContent) {
                if ("role".equalsIgnoreCase(name)) {
                    return ((ChatMessageContent) context).getAuthorRole().name();
                } else if ("content".equalsIgnoreCase(name)) {
                    return ((ChatMessageContent) context).getContent();
                }
            }
            return UNRESOLVED;
        }

        @Override
        public Object resolve(Object context) {
            if (context instanceof ChatMessageContent) {
                String result = ((ChatMessageContent) context).getContent();
                return result != null ? result : UNRESOLVED;
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
            if (context instanceof KernelFunction) {
                KernelFunction<?> function = (KernelFunction<?>) context;
                if ("pluginname".equalsIgnoreCase(name)) {
                    if (function.getPluginName() != null) {
                        return function.getPluginName();
                    }
                } else if ("name".equalsIgnoreCase(name)) {
                    return function.getName();
                }
            }
            return UNRESOLVED;
        }

        @Override
        public Object resolve(Object context) {
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
            Object value = null;
            if (context instanceof KernelFunctionArguments) {
                ContextVariable<?> variable = ((KernelFunctionArguments) context).get(name);
                value = variable != null ? variable.getValue() : null;
            }
            if (context instanceof ContextVariable) {
                value = ((ContextVariable<?>) context).getValue();
            }
            if (value == null) {
                return UNRESOLVED;
            } else {
                return value;
            }
        }

        @Override
        public Object resolve(Object context) {
            if (context instanceof ContextVariable) {
                Object result = ((ContextVariable<?>) context).getValue();
                return result != null ? result : UNRESOLVED;
            }
            return UNRESOLVED;
        }

        @Override
        public Set<Entry<String, Object>> propertySet(Object context) {
            if (context instanceof KernelFunctionArguments) {
                HashMap<String, Object> result = new HashMap<>();
                result.putAll((KernelFunctionArguments) context);
                return result.entrySet();
            } else if (context instanceof ContextVariable) {
                HashMap<String, Object> result = new HashMap<>();
                result.put("value", ((ContextVariable<?>) context).getValue());
                return result.entrySet();
            }
            return new HashSet<>();
        }
    }

    private static class HandleBarsPromptTemplateHandler {

        private final String template;
        private final Handlebars handlebars;

        @SuppressFBWarnings("CT_CONSTRUCTOR_THROW") // Think this is a false positive
        public HandleBarsPromptTemplateHandler(Kernel kernel, String template) {
            this.template = template;
            this.handlebars = new Handlebars();
            this.handlebars
                .registerHelper("message", HandleBarsPromptTemplateHandler::handleMessage)
                .registerHelper("each", HandleBarsPromptTemplateHandler::handleEach)
                .registerHelper("functions", (context, options) -> handleFunctions(kernel, options))
                .registerHelper("function",
                    (context, options) -> handleFunction((KernelFunction<?>) context));
            // TODO: 1.0 Add more helpers
        }

        private static Handlebars.SafeString handleFunction(KernelFunction<?> context) {
            KernelFunction<?> function = context;
            String pluginName = function.getPluginName();
            String functionName = function.getName();
            String description = function.getDescription();
            StringBuilder sb = new StringBuilder(
                String.format(
                    "<function pluginName=\"%s\" name=\"%s\" description=\"%s\">",
                    pluginName, functionName, description));
            List<KernelParameterMetadata<?>> parameters = function.getMetadata().getParameters();
            parameters.forEach(p -> {
                sb.append(String.format(
                    "<parameter name=\"%s\" description=\"%s\" defaultValue=\"%s\" isRequired=\"%s\" type=\"%s\"/>",
                    p.getName(), p.getDescription(), p.getDefaultValue(), p.isRequired(),
                    p.getType()));
            });
            sb.append("</function>");
            return new Handlebars.SafeString(sb.toString());
        }

        private static Handlebars.SafeString handleFunctions(Kernel kernel, Options options)
            throws IOException {
            StringBuilder sb = new StringBuilder("<functions>");
            Collection<KernelPlugin> plugins = kernel.getPlugins();
            sb.append(options.fn(plugins));
            sb.append("</functions>");

            return new Handlebars.SafeString(sb.toString());
        }

        private static CharSequence handleEach(Object context, Options options)
            throws IOException {
            if (context instanceof ChatHistory) {
                StringBuilder sb = new StringBuilder("<messages>");
                for (ChatMessageContent message : (ChatHistory) context) {
                    sb.append(options.fn(message));
                }
                sb.append("</messages>");
                return new Handlebars.SafeString(sb.toString());
            }
            if (context instanceof List) {
                StringBuilder sb = new StringBuilder();
                Iterator<?> iterator = ((List<?>) context).iterator();
                while (iterator.hasNext()) {
                    Object element = iterator.next();
                    if (element instanceof KernelPlugin) {
                        KernelPlugin plugin = (KernelPlugin) element;
                        Iterator<KernelFunction<?>> functions = plugin.iterator();
                        while (functions.hasNext()) {
                            KernelFunction<?> function = functions.next();
                            sb.append(options.fn(function));
                        }
                    }
                }
                return new Handlebars.SafeString(sb.toString());
            }
            return "";
        }

        private static CharSequence handleMessage(Object context, Options options)
            throws IOException {
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

        public Mono<String> render(KernelFunctionArguments variables) {
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
