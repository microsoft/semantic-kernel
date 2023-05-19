// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.builders;

import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.ServiceLoader;

class ServiceLoadUtil {
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
            // ignore
        }

        throw new RuntimeException("Service not found: " + clazz.getName());
    }

    public static <T> List<T> findAllServiceLoaders(Class<T> clazz) {
        List<T> serviceLoaders = new ArrayList<T>();

        ServiceLoader<T> factory = ServiceLoader.load(clazz);
        Iterator<T> iterator = factory.iterator();
        iterator.forEachRemaining(serviceLoaders::add);

        return serviceLoaders;
    }
}
