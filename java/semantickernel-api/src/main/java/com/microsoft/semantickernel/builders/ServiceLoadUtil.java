// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.ServiceLoader;

public class ServiceLoadUtil {
    private static final Logger LOGGER = LoggerFactory.getLogger(ServiceLoadUtil.class);

    private ServiceLoadUtil() {}

    public static <T> T findServiceLoader(Class<T> clazz, String alternativeClassName) {
        List<T> services = findAllServiceLoaders(clazz);
        if (services.size() > 0) {
            return services.get(0);
        }

        try {
            // Service loader not found, attempt to load the alternative class
            Object instance =
                    Class.forName(alternativeClassName).getDeclaredConstructor().newInstance();
            if (clazz.isInstance(instance)) {
                return (T) instance;
            }
        } catch (ClassNotFoundException
                | InvocationTargetException
                | InstantiationException
                | IllegalAccessException
                | NoSuchMethodException
                | RuntimeException e) {
            LOGGER.error("Unable to load service " + clazz.getName() + " ", e);
        }

        throw new RuntimeException("Service not found: " + clazz.getName());
    }

    static <T> List<T> findAllServiceLoaders(Class<T> clazz) {
        List<T> serviceLoaders = new ArrayList<T>();

        ServiceLoader<T> factory = ServiceLoader.load(clazz);
        Iterator<T> iterator = factory.iterator();
        iterator.forEachRemaining(serviceLoaders::add);

        return serviceLoaders;
    }
}
