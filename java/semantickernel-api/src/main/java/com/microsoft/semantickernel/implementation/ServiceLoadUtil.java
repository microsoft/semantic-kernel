// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.ServiceLoader;
import java.util.function.Supplier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * This class is used for loading services that are not directly referenced
 * in the code, but are instead loaded using the ServiceLoader pattern.
 *
 */
public class ServiceLoadUtil {

    private static final Logger LOGGER = LoggerFactory.getLogger(ServiceLoadUtil.class);

    private ServiceLoadUtil() {
    }

    /**
     * Finds a service loader for the given class and returns a supplier for it.
     *
     * @param clazz The class to find a service loader for.
     * @param <T>   The type of the class to find a service loader for.
     * @param alternativeClassName The name of the alternative class to load if the service loader
     *                            is not found.
     * @return A {@code java.util.function.Supplier} for the service loader.
     */
    public static <T>
    Supplier<T> findServiceLoader(Class<T> clazz, String alternativeClassName) {
        List<T> services = findAllServiceLoaders(clazz);

        T impl = null;

        if (services.size() > 0) {
            impl = services.get(0);
        }

        if (impl == null) {
            try {
                // Service loader not found, attempt to load the alternative class
                Object instance =
                    Class.forName(alternativeClassName).getDeclaredConstructor().newInstance();
                if (clazz.isInstance(instance)) {
                    impl = (T) instance;
                }
            } catch (ClassNotFoundException
                     | InvocationTargetException
                     | InstantiationException
                     | IllegalAccessException
                     | NoSuchMethodException
                     | RuntimeException e) {
                LOGGER.error("Unable to load service " + clazz.getName() + " ", e);
            }

            if (impl == null) {
                throw new RuntimeException("Service not found: " + clazz.getName());
            }
        }

        try {
            Constructor<?> constructor = impl.getClass().getConstructor();

            // Test that we can construct the builder
            if (!clazz.isInstance(constructor.newInstance())) {
                throw new RuntimeException(
                    "Builder creates instance of the wrong type: " + clazz.getName());
            }

            return () -> {
                try {
                    return (T) constructor.newInstance();
                } catch (InstantiationException
                         | IllegalAccessException
                         | InvocationTargetException e) {
                    throw new RuntimeException(e);
                }
            };
        } catch (NoSuchMethodException e) {
            throw new RuntimeException(
                "Builder requires a no args constructor: " + clazz.getName());
        } catch (InvocationTargetException | InstantiationException | IllegalAccessException e) {
            throw new RuntimeException("Builder is of wrong type: " + clazz.getName());
        }
    }

    static <T> List<T> findAllServiceLoaders(Class<T> clazz) {
        List<T> serviceLoaders = new ArrayList<T>();

        ServiceLoader<T> factory = ServiceLoader.load(clazz);
        Iterator<T> iterator = factory.iterator();
        iterator.forEachRemaining(serviceLoaders::add);

        return serviceLoaders;
    }
}
