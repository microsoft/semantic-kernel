// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import java.util.HashMap;
import java.util.Map;
import java.util.function.BiFunction;
import java.util.function.Function;
import java.util.stream.Collectors;

public class CaseInsensitiveMap<T> extends HashMap<String, T> {
    public CaseInsensitiveMap(Map<String, T> kvMap) {
        super();
        putAll(kvMap);
    }

    public CaseInsensitiveMap() {
        super();
    }

    @Override
    public T computeIfAbsent(String key, Function<? super String, ? extends T> mappingFunction) {
        if (key == null) {
            return super.computeIfAbsent(null, mappingFunction);
        }
        return super.computeIfAbsent(key.toLowerCase(), mappingFunction);
    }

    @Override
    public T computeIfPresent(
            String key, BiFunction<? super String, ? super T, ? extends T> remappingFunction) {
        if (key == null) {
            return super.computeIfPresent(null, remappingFunction);
        }
        return super.computeIfPresent(key.toLowerCase(), remappingFunction);
    }

    @Override
    public T compute(
            String key, BiFunction<? super String, ? super T, ? extends T> remappingFunction) {
        if (key == null) {
            return super.compute(null, remappingFunction);
        }
        return super.compute(key.toLowerCase(), remappingFunction);
    }

    @Override
    public boolean containsKey(Object key) {
        if (key == null) {
            return super.containsKey(null);
        }
        return super.containsKey(((String) key).toLowerCase());
    }

    @Override
    public T get(Object key) {
        if (key == null) {
            return super.get(null);
        }
        return super.get(((String) key).toLowerCase());
    }

    @Override
    public T getOrDefault(Object key, T defaultValue) {
        if (key == null) {
            return super.getOrDefault(null, defaultValue);
        }
        return super.getOrDefault(((String) key).toLowerCase(), defaultValue);
    }

    @Override
    public T merge(
            String key, T value, BiFunction<? super T, ? super T, ? extends T> remappingFunction) {
        if (key == null) {
            return super.merge(null, value, remappingFunction);
        }
        return super.merge(key.toLowerCase(), value, remappingFunction);
    }

    @Override
    public T put(String key, T value) {
        if (key == null) {
            return super.put(null, value);
        }
        return super.put(key.toLowerCase(), value);
    }

    @Override
    public void putAll(Map<? extends String, ? extends T> m) {
        super.putAll(
                m.entrySet().stream()
                        .collect(
                                Collectors.toMap(
                                        key -> key.getKey().toLowerCase(), Entry::getValue)));
    }

    @Override
    public T putIfAbsent(String key, T value) {
        if (key == null) {
            return super.putIfAbsent(null, value);
        }
        return super.putIfAbsent(key.toLowerCase(), value);
    }

    @Override
    public boolean remove(Object key, Object value) {
        if (key == null) {
            return super.remove(null, value);
        }
        return super.remove(((String) key).toLowerCase(), value);
    }

    @Override
    public T remove(Object key) {
        if (key == null) {
            return super.remove(null);
        }
        return super.remove(((String) key).toLowerCase());
    }

    @Override
    public boolean replace(String key, T oldValue, T newValue) {

        if (key == null) {
            return super.replace(null, oldValue, newValue);
        }
        return super.replace(key.toLowerCase(), oldValue, newValue);
    }

    @Override
    public T replace(String key, T value) {
        if (key == null) {
            return super.replace(null, value);
        }
        return super.replace(key.toLowerCase(), value);
    }
}
