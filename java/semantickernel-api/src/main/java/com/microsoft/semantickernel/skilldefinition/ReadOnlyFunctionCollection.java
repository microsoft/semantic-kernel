// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.orchestration.SKFunction;
import java.util.List;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

public interface ReadOnlyFunctionCollection {

    String getSkillName();

    SKFunction<?> getFunction(String functionName);

    /**
     * Get function with the given SKFunction type argument.
     *
     * @param functionName the name of the function to retrieve
     * @param clazz The class of the SKFunction parameter type
     * @param <T> SKFunction parameter type
     * @return The given function
     * @throws RuntimeException if the given entry is not of the expected type
     */
    <T extends SKFunction> T getFunction(String functionName, @Nullable Class<T> clazz);

    /**
     * @return A clone of this collection
     */
    @CheckReturnValue
    ReadOnlyFunctionCollection copy();

    /**
     * @return An unmodifiable list of all functions
     */
    List<SKFunction<?>> getAll();
}
