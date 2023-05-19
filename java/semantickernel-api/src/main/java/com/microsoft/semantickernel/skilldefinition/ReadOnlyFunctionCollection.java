// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.orchestration.SKFunction;

import java.util.*;
import java.util.stream.Collectors;

import javax.annotation.CheckReturnValue;

/**
 * A collection of functions. This is read only, write operations return a clone of the collection
 */
public class ReadOnlyFunctionCollection {
    private final Map<String, SKFunction<?, ?>> functionCollection;

    private final String skillName;

    private ReadOnlyFunctionCollection(
            String skillName, Map<String, SKFunction<?, ?>> functionCollection) {
        this.functionCollection = Collections.unmodifiableMap(functionCollection);
        this.skillName = skillName;
    }

    public ReadOnlyFunctionCollection(
            String skillName, List<? extends SKFunction<?, ?>> functionCollection) {
        this(
                skillName,
                functionCollection.stream()
                        .collect(Collectors.toMap(it -> it.getName().toLowerCase(), it -> it)));
    }

    public ReadOnlyFunctionCollection(String skillName) {
        this.skillName = skillName;
        this.functionCollection = new HashMap<>();
    }

    public String getSkillName() {
        return skillName;
    }

    public SKFunction<?, ?> getFunction(String functionName) {
        SKFunction<?, ?> func = functionCollection.get(functionName.toLowerCase());
        if (func == null) {
            throw new FunctionNotFound();
        }
        return func;
    }

    /**
     * Get function with the given SKFunction type argument.
     *
     * @param functionName the name of the function to retrieve
     * @param clazz The class of the SKFunction parameter type
     * @param <T> SKFunction parameter type
     * @return The given function
     * @throws RuntimeException if the given entry is not of the expected type
     */
    public <T extends SKFunction> T getFunction(String functionName, Class<T> clazz) {
        SKFunction<?, ?> func = getFunction(functionName);
        if (clazz.isInstance(func)) {
            return (T) func;
        } else {
            throw new RuntimeException("Incorrect type requested");
        }
    }

    /**
     * Add function to the collection overwriting existing function
     *
     * @param functionName
     * @param functionInstance
     * @return A clone of this collection with the function added
     */
    @CheckReturnValue
    public ReadOnlyFunctionCollection put(String functionName, SKFunction<?, ?> functionInstance) {
        HashMap<String, SKFunction<?, ?>> functionCollection =
                new HashMap<>(this.functionCollection);
        functionCollection.put(functionName.toLowerCase(), functionInstance);

        return new ReadOnlyFunctionCollection(skillName, functionCollection);
    }

    /**
     * @return A clone of this collection
     */
    @CheckReturnValue
    public ReadOnlyFunctionCollection copy() {
        return new ReadOnlyFunctionCollection(skillName, functionCollection);
    }

    /**
     * @return An unmodifiable list of all functions
     */
    public List<SKFunction<?, ?>> getAll() {
        return Collections.unmodifiableList(new ArrayList<>(functionCollection.values()));
    }

    /**
     * Merge in the given collection to this one, duplicate function names will overwrite
     *
     * @param value
     * @return a clone of this collection with the new entries added
     */
    public ReadOnlyFunctionCollection merge(ReadOnlyFunctionCollection value) {
        HashMap<String, SKFunction<?, ?>> mutable = new HashMap<>(functionCollection);

        mutable.putAll(value.functionCollection);

        return new ReadOnlyFunctionCollection(skillName, mutable);
    }
}
