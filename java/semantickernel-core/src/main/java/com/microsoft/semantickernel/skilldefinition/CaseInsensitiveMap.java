// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import java.util.HashMap;
import java.util.Map;
import java.util.function.BiFunction;
import java.util.function.Function;
import java.util.stream.Collectors;

class CaseInsensitiveMap<T> extends HashMap<String, T> {
    public CaseInsensitiveMap(Map<String, T> kvMap) {
        super();
        putAll(kvMap);
    }

    public CaseInsensitiveMap() {
        super();
    }

    @Override
    public T computeIfAbsent(String key, Function<? super String, ? extends T> mappingFunction) {
        return super.computeIfAbsent(key.toLowerCase(), mappingFunction);
    }

    @Override
    public T computeIfPresent(
            String key, BiFunction<? super String, ? super T, ? extends T> remappingFunction) {
        return super.computeIfPresent(key.toLowerCase(), remappingFunction);
    }

    @Override
    public T compute(
            String key, BiFunction<? super String, ? super T, ? extends T> remappingFunction) {
        return super.compute(key.toLowerCase(), remappingFunction);
    }

    @Override
    public boolean containsKey(Object key) {
        return super.containsKey(((String) key).toLowerCase());
    }

    @Override
    public T get(Object key) {
        return super.get(((String) key).toLowerCase());
    }

    @Override
    public T getOrDefault(Object key, T defaultValue) {
        return super.getOrDefault(((String) key).toLowerCase(), defaultValue);
    }

    @Override
    public T merge(
            String key, T value, BiFunction<? super T, ? super T, ? extends T> remappingFunction) {
        return super.merge(key.toLowerCase(), value, remappingFunction);
    }

    @Override
    public T put(String key, T value) {
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
        return super.putIfAbsent(key.toLowerCase(), value);
    }

    @Override
    public boolean remove(Object key, Object value) {
        return super.remove(((String) key).toLowerCase(), value);
    }

    @Override
    public T remove(Object key) {
        return super.remove(((String) key).toLowerCase());
    }

    @Override
    public boolean replace(String key, T oldValue, T newValue) {
        return super.replace(key.toLowerCase(), oldValue, newValue);
    }

    @Override
    public T replace(String key, T value) {
        return super.replace(key.toLowerCase(), value);
    }
}
