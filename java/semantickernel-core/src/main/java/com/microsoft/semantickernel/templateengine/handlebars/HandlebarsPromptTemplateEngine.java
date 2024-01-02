// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.templateengine.handlebars;

/*
public class HandlebarsPromptTemplateEngine implements PromptTemplateEngine {

    public HandlebarsPromptTemplateEngine(PromptTemplateConfig promptConfig) {
    }

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

    private static class MessageResolver implements ValueResolver {

        @Override
        public Object resolve(Object context, String name) {
            if (context instanceof Message) {
                if ("role".equals(name.toLowerCase())) {
                    return ((Message) context).getAuthorRoles().name();
                } else if ("content".equals(name.toLowerCase())) {
                    return ((Message) context).getContent();
                }
            }
            return UNRESOLVED;
        }

        @Override
        public Object resolve(Object context) {
            if (context instanceof Message) {
                return ((Message) context).getContent();
            }
            return UNRESOLVED;
        }

        @Override
        public Set<Entry<String, Object>> propertySet(Object context) {
            if (context instanceof Message) {
                HashMap<String, Object> result = new HashMap<>();
                result.put("role", ((Message) context).getAuthorRoles().name());
                result.put("content", ((Message) context).getContent());
                return result.entrySet();
            }
            return new HashSet<>();
        }
    }

    private static class ContextVariableResolver implements ValueResolver {

        @Override
        public Object resolve(Object context, String name) {
            if (context instanceof ContextVariables) {
                return ((ContextVariables) context).get(name).getValue();
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
            if (context instanceof ContextVariables) {
                HashMap<String, Object> result = new HashMap<>();
                result.putAll((ContextVariables) context);
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
                new Helper<Object>() {
                    @Override
                    public Object apply(Object context, Options options) throws IOException {
                        String role = options.hash("role");
                        String content = (String) options.fn(context);

                        if (context instanceof Optional) {
                            ChatHistory.Message message = ((Optional<ChatHistory.Message>) context).orElse(
                                null);
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

            //            AtomicReference<String> template = new AtomicReference<>(this.template);
            //
            //            variables
            //                    .asMap()
            //                    .forEach(
            //                            (k, v) -> {
            //                                try {
            //                                    template.set(
            //
            // handlebars.compileInline(template.get()).apply(v));
            //                                } catch (IOException e) {
            //                                    throw new RuntimeException(e);
            //                                }
            //                            });
            //
            //            return Mono.just(template.get());
        }
    }
}
*/