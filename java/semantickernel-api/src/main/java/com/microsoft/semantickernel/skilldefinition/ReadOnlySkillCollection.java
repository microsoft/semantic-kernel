// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.SKFunction;
import java.util.Map;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

/**
 * Skill collection interface.
 *
 * <p>This is read only
 */
public interface ReadOnlySkillCollection extends Buildable {

    String GlobalSkill = "_GLOBAL_FUNCTIONS_";

    @CheckReturnValue
    ReadOnlySkillCollection copy();

    /*
      /// <summary>
      /// Add a native function to the collection
      /// </summary>
      /// <param name="functionInstance">Wrapped function delegate</param>
      /// <returns>Self instance</returns>
    */

    /** Get this collection as an unmodifiable map */
    Map<String, ReadOnlyFunctionCollection> asMap();

    ReadOnlyFunctionCollection getAllFunctions();

    /** Get function with name from the global scope */
    @Nullable
    <T extends SKFunction<?>> T getFunction(String functionName, @Nullable Class<T> functionType);

    @Nullable
    <T extends SKFunction<?>> T getFunction(
            String skillName, String funName, @Nullable Class<T> functionClazz);

    @Nullable
    ReadOnlyFunctionCollection getFunctions(String skillName);

    boolean hasFunction(String functionName);

    boolean hasFunction(String skillName, String functionName);

    static Builder builder() {
        return BuildersSingleton.INST.getInstance(Builder.class);
    }

    interface Builder extends SemanticKernelBuilder<ReadOnlySkillCollection> {}
}
