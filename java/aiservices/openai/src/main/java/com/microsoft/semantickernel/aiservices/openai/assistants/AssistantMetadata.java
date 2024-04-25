package com.microsoft.semantickernel.aiservices.openai.assistants;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public class AssistantMetadata implements Map<String, String> {

    private final Map<String, String> metadata;

    public AssistantMetadata() {
        this.metadata = new HashMap<>();
    }

    @Override
    public int size() {
        return metadata.size();
    }

    @Override
    public boolean isEmpty() {
        return metadata.isEmpty();
    }

    @Override
    public boolean containsKey(Object key) {
        return metadata.containsKey(key);
    }

    @Override
    public boolean containsValue(Object value) {
        return metadata.containsValue(value);
    }

    @Override
    public String get(Object key) {
        return metadata.get(key);
    }

    @Override
    public String put(String key, String value) {
        if (key.length() > 64 || value.length() > 512) {
            throw new IllegalArgumentException("Key must be 64 characters or less and value must be 512 characters or less");
        }
        if (metadata.size() >= 16) {
            throw new IllegalArgumentException("Metadata can only contain 16 key-value pairs");
        }
        return metadata.put(key, value);
    }

    @Override
    public String remove(Object key) {
        return metadata.remove(key);
    }

    @Override
    public void putAll(Map<? extends String, ? extends String> m) {
        m.entrySet().forEach(entry -> put(entry.getKey(), entry.getValue()));
    }

    @Override
    public void clear() {
        metadata.clear();
    }

    @Override
    public Set<String> keySet() {
        return metadata.keySet();
    }

    @Override
    public Collection<String> values() {
        return metadata.values();
    }

    @Override
    public Set<Entry<String, String>> entrySet() {
        return metadata.entrySet();
    }

    @Override
    public boolean equals(Object o) {
        return metadata.equals(o);
    }

    @Override
    public int hashCode() {
        return metadata.hashCode();
    }

    @Override
    public String toString() {
        return metadata.toString();
    }

}
