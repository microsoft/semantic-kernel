// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.SKFunction;

import java.util.Map;

import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

/**
 * Skill collection interface.
 *
 * <p>This is read only, write operations will return a modified result
 */
public interface ReadOnlySkillCollection {

    String GlobalSkill = "_GLOBAL_FUNCTIONS_";

    /**
     * Add a semantic function to the collection
     *
     * @param functionInstance function to add
     * @return Modified clone of this collection with function added
     */
    @CheckReturnValue
    ReadOnlySkillCollection addSemanticFunction(SKFunction<?, ?> functionInstance);

    @CheckReturnValue
    ReadOnlySkillCollection copy();

    /*
      /// <summary>
      /// Add a native function to the collection
      /// </summary>
      /// <param name="functionInstance">Wrapped function delegate</param>
      /// <returns>Self instance</returns>
    */

    /**
     * Add a native function to the collection
     *
     * @param functionInstance function to add
     * @return Modified clone of this collection with function added
     */
    @CheckReturnValue
    ReadOnlySkillCollection addNativeFunction(SKFunction functionInstance);

    /** Merge in the collection, the function collections of duplicate keys are concatenated */
    @CheckReturnValue
    ReadOnlySkillCollection merge(ReadOnlySkillCollection in);

    /** Get this collection as an unmodifiable map */
    Map<String, ReadOnlyFunctionCollection> asMap();

    ReadOnlyFunctionCollection getAllFunctions();

    /** Get function with name from the global scope */
    @Nullable
    <T extends SKFunction<?, ?>> T getFunction(String functionName, Class<T> functionType);

    @Nullable
    <T extends SKFunction<?, ?>> T getFunction(
            String skillName, String funName, Class<T> functionClazz);

    @Nullable
    ReadOnlyFunctionCollection getFunctions(String skillName);

    public interface Builder {
        public ReadOnlySkillCollection build();
    }
}
