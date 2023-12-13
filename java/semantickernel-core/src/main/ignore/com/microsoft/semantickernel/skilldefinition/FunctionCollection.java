// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.exceptions.SkillsNotFoundException;
import com.microsoft.semantickernel.exceptions.SkillsNotFoundException.ErrorCodes;
import com.microsoft.semantickernel.orchestration.KernelFunction;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

/** A collection of functions. */
public class FunctionCollection implements ReadOnlyFunctionCollection {
    private final CaseInsensitiveMap<KernelFunction> functionCollection;

    private final String skillName;

    private FunctionCollection(String skillName, Map<String, KernelFunction> functionCollection) {
        this.functionCollection = new CaseInsensitiveMap<>(functionCollection);
        this.skillName = skillName;
    }

    public FunctionCollection(String skillName, List<? extends KernelFunction> functionCollection) {
        this(
                skillName,
                functionCollection.stream()
                        .collect(
                                Collectors.toMap(
                                        it -> it.getName().toLowerCase(Locale.ROOT), it -> it)));
    }

    public FunctionCollection(String skillName) {
        this.skillName = skillName;
        this.functionCollection = new CaseInsensitiveMap<>();
    }

    public FunctionCollection(ReadOnlyFunctionCollection value) {
        this.skillName = value.getSkillName();
        this.functionCollection =
                new CaseInsensitiveMap<KernelFunction>(
                        Collections.unmodifiableMap(
                                value.getAll().stream()
                                        .collect(Collectors.toMap(KernelFunction::getName, it -> it))));
    }

    @Override
    public String getSkillName() {
        return skillName;
    }

    @Override
    public KernelFunction getFunction(String functionName) {
        KernelFunction func = functionCollection.get(functionName.toLowerCase(Locale.ROOT));
        if (func == null) {
            throw new FunctionNotFound(
                    FunctionNotFound.ErrorCodes.FUNCTION_NOT_FOUND, functionName);
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
    @Override
    public <T extends KernelFunction> T getFunction(String functionName, @Nullable Class<T> clazz) {
        KernelFunction func = getFunction(functionName);
        if (clazz == null) {
            return (T) func;
        }
        if (clazz.isInstance(func)) {
            return (T) func;
        } else {
            throw new SkillsNotFoundException(
                    ErrorCodes.SKILLS_NOT_FOUND,
                    "Incorrect type requested, expected type of "
                            + clazz.getName()
                            + " found class of type "
                            + func.getClass().getName());
        }
    }

    /**
     * @return A clone of this collection
     */
    @Override
    @CheckReturnValue
    public FunctionCollection copy() {
        return new FunctionCollection(skillName, functionCollection);
    }

    /**
     * @return An unmodifiable list of all functions
     */
    @Override
    public List<KernelFunction> getAll() {
        return Collections.unmodifiableList(new ArrayList<>(functionCollection.values()));
    }

    /**
     * Add function to the collection overwriting existing function
     *
     * @param functionName
     * @param functionInstance
     * @return Collection for fluent callse
     */
    public FunctionCollection put(String functionName, KernelFunction functionInstance) {
        this.functionCollection.put(functionName.toLowerCase(Locale.ROOT), functionInstance);
        return this;
    }

    /**
     * Merge in the given collection to this one, duplicate function names will overwrite
     *
     * @param value
     * @return Collection for fluent calls
     */
    public FunctionCollection merge(FunctionCollection value) {
        functionCollection.putAll(value.functionCollection);
        return this;
    }
}
