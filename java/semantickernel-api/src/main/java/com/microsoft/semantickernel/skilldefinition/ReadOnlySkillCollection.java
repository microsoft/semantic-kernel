// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.orchestration.SKFunction;
import java.util.Map;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

/**
 * Skill collection interface.
 *
 * <p>This is read only
 */
public interface ReadOnlySkillCollection {

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

    public interface Builder {
        public ReadOnlySkillCollection build();
    }
}
