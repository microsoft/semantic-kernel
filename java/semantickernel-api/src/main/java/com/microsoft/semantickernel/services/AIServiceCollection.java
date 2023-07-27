// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.services;

import com.microsoft.semantickernel.Verify;
import com.microsoft.semantickernel.ai.embeddings.EmbeddingGeneration;
import com.microsoft.semantickernel.ai.embeddings.TextEmbeddingGeneration;
import com.microsoft.semantickernel.chatcompletion.ChatCompletion;
import com.microsoft.semantickernel.textcompletion.TextCompletion;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

/** A collection that can hold AI services */
public class AIServiceCollection {
    // A constant key for the default service
    private static final String DefaultKey = "__DEFAULT__";

    private static final List<Class<? extends AIService>> KNOWN_SERVICES =
            Arrays.asList(
                    EmbeddingGeneration.class,
                    TextEmbeddingGeneration.class,
                    TextCompletion.class,
                    ChatCompletion.class);

    // A dictionary that maps a service type to a nested dictionary of names and service instances
    // or factories
    // private readonly Dictionary<Type, Dictionary<string, object>> _services = new();
    private final Map<Class<? extends AIService>, Map<String, Supplier<? extends AIService>>>
            services = new HashMap<>();

    // A dictionary that maps a service type to the name of the default service
    private final Map<Class<? extends AIService>, String> defaultIds = new HashMap<>();

    /**
     * Registers a singleton service instance with the default name.
     *
     * @param service The service instance.
     * @param serviceType The type of the service.
     */
    public <T extends AIService> void setService(T service, Class<T> serviceType) {
        setService(DefaultKey, (Supplier<T>) () -> service, true, serviceType);
    }

    /**
     * Registers a singleton service instance with an optional name and default flag.
     *
     * @param name The name of the service, or null for the default service.
     * @param service The service instance.
     * @param setAsDefault Whether the service should be the default for its type.
     * @param serviceType The type of the service.
     */
    public <T extends AIService> void setService(
            String name, T service, boolean setAsDefault, Class<T> serviceType) {
        setService(name, (Supplier<T>) () -> service, setAsDefault, serviceType);
    }

    /**
     * Registers a transient service factory with the default name.
     *
     * @param factory The factory function to create the service instance.
     * @param serviceType The type of the service.
     */
    public <T extends AIService> void setService(Supplier<T> factory, Class<T> serviceType) {
        setService(DefaultKey, factory, true, serviceType);
    }

    /**
     * Registers a transient service factory with an optional name and default flag.
     *
     * @param name The name of the service, or null for the default service.
     * @param factory The factory function to create the service instance.
     * @param setAsDefault Whether the service should be the default for its type.
     * @param specificServiceType The type of the service.
     */
    public <T extends AIService> void setService(
            @Nullable String name,
            Supplier<T> factory,
            boolean setAsDefault,
            Class<T> specificServiceType) {

        // Validate the factory function
        if (factory == null) {
            throw new IllegalArgumentException();
        }

        // if this is an implementation of a known service type, register it as such
        getKnownServiceTypes(specificServiceType)
                .forEach(
                        serviceType -> {
                            // Get or create the nested dictionary for the service type
                            Map<String, Supplier<? extends AIService>> namedServices =
                                    this.services.computeIfAbsent(
                                            serviceType, (ignore) -> new HashMap<>());

                            // Set as the default if the name is empty, or the default flag is true,
                            // or there is no default name for the service type.
                            if (name == null || setAsDefault || !this.hasDefault(serviceType)) {
                                // Update the default name for the service type
                                this.defaultIds.put(serviceType, name == null ? DefaultKey : name);
                            }

                            // Register the factory with the given name
                            namedServices.put(name == null ? DefaultKey : name, factory);
                        });
    }

    private <T extends AIService> List<Class<? extends AIService>> getKnownServiceTypes(
            Class<T> serviceType) {
        ArrayList<Class<? extends AIService>> knownServices =
                KNOWN_SERVICES.stream()
                        .filter(knownServiceType -> knownServiceType.isAssignableFrom(serviceType))
                        .collect(Collectors.toCollection(ArrayList::new));

        knownServices.add(serviceType);
        return knownServices;
    }

    /**
     * Builds an AIServiceProvider from the registered services and default names.
     *
     * @return The AIServiceProvider.
     */
    public AIServiceProvider build() {
        // Create a clone of the services and defaults Dictionaries to prevent further changes
        // by the services provider.
        Map<Class<? extends AIService>, Map<String, Supplier<? extends AIService>>> servicesClone =
                cloneServices(services);

        Map defaultsClone = new HashMap<>(defaultIds);

        return new DefaultAIServiceProvider(servicesClone, defaultsClone);
    }

    /**
     * Creates a clone of the services as a Map.
     *
     * @param services The services Map.
     * @return The clone.
     */
    static <T> Map<Class<? extends T>, Map<String, Supplier<? extends T>>> cloneServices(
            Map<Class<? extends T>, Map<String, Supplier<? extends T>>> services) {
        return Collections.unmodifiableMap(
                services.entrySet().stream()
                        .reduce(
                                new HashMap<>(),
                                (a, b) -> {
                                    a.put(b.getKey(), Collections.unmodifiableMap(b.getValue()));
                                    return a;
                                },
                                (a, b) -> {
                                    a.putAll(b);
                                    return a;
                                }));
    }

    private <T extends AIService> boolean hasDefault(Class<T> type) {
        String defaultName = defaultIds.get(type);
        return !Verify.isNullOrEmpty(defaultName);
    }
}
