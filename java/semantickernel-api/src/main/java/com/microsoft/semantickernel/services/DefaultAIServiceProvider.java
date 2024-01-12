// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import java.util.Map;
import java.util.function.Supplier;

/** Default implementation of {@link AIServiceProvider} */
public class DefaultAIServiceProvider extends DefaultNamedServiceProvider<AIService>
        implements AIServiceProvider {
    public DefaultAIServiceProvider(
            Map<Class<? extends AIService>, Map<String, Supplier<? extends AIService>>> services,
            Map<Class<? extends AIService>, String> defaultIds) {
        super(services, defaultIds);
    }
}
