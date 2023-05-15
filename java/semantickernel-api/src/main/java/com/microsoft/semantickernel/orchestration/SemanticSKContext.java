// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;
// Copyright (c) Microsoft. All rights reserved.

/**
 * Semantic Kernel context.
 *
 * <p>This is read only, write operations will return a modified result
 */
public interface SemanticSKContext extends SKContext<SemanticSKContext> {
    /*
       static <T> NOPSKContext<T> build(
               ReadOnlyContextVariables variables,
               SemanticTextMemory memory,
               Supplier<ReadOnlySkillCollection> skills) {
           return (NOPSKContext<T>) new ImmutableReadOnlySKContext(variables, memory, skills);
       }

    */
}
