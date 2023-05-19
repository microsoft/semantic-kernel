// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.SKFunction;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

import javax.annotation.CheckReturnValue;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/// <summary>
/// Semantic Kernel default skill collection class.
/// The class holds a list of all the functions, native and semantic, known to the kernel instance.
/// The list is used by the planner and when executing pipelines of function compositions.
/// </summary>
// [System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1710:Identifiers should have
// correct suffix", Justification = "It is a collection")]
// [System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have
// incorrect suffix", Justification = "It is a collection")]
public class DefaultSkillCollection implements ReadOnlySkillCollection {

    private final CaseInsensitiveMap<FunctionCollection> skillCollection;

    public static class Builder implements ReadOnlySkillCollection.Builder {
        @Override
        public ReadOnlySkillCollection build() {
            return new DefaultSkillCollection();
        }
    }

    protected Map<String, FunctionCollection> getSkillCollection() {
        return skillCollection;
    }

    public DefaultSkillCollection(ReadOnlySkillCollection skillCollection) {
        this(skillCollection.asMap());
    }

    public DefaultSkillCollection(
            Map<String, ? extends ReadOnlyFunctionCollection> skillCollection) {

        Map<String, FunctionCollection> cloned =
                skillCollection.entrySet().stream()
                        .collect(
                                Collectors
                                        .<Map.Entry<String, ? extends ReadOnlyFunctionCollection>,
                                                String, FunctionCollection>
                                                toMap(
                                                        Map.Entry::getKey,
                                                        it ->
                                                                new FunctionCollection(
                                                                        it.getValue())));

        this.skillCollection = new CaseInsensitiveMap<>(cloned);
    }

    public DefaultSkillCollection() {
        this.skillCollection = new CaseInsensitiveMap<>();
    }

    @CheckReturnValue
    public DefaultSkillCollection addSemanticFunction(SKFunction functionInstance) {
        FunctionCollection existingFunctionCollection;
        if (!skillCollection.containsKey(functionInstance.getSkillName().toLowerCase())) {
            existingFunctionCollection =
                    new FunctionCollection(functionInstance.getSkillName().toLowerCase());
        } else {
            existingFunctionCollection =
                    skillCollection.get(functionInstance.getSkillName().toLowerCase());
        }

        existingFunctionCollection =
                existingFunctionCollection.put(
                        functionInstance.getName().toLowerCase(), functionInstance);

        HashMap<String, FunctionCollection> clonedSkillCollection = new HashMap<>(skillCollection);

        clonedSkillCollection.put(
                functionInstance.getSkillName().toLowerCase(), existingFunctionCollection);

        return new DefaultSkillCollection(clonedSkillCollection);
    }

    @Override
    @Nullable
    public <T extends SKFunction<?, ?>> T getFunction(
            String funName, @Nonnull Class<T> functionClazz) {
        return getFunction(GlobalSkill, funName, functionClazz);
    }

    @Override
    @Nullable
    public <T extends SKFunction<?, ?>> T getFunction(
            String skillName, String funName, Class<T> functionClazz) {
        FunctionCollection skills = skillCollection.get(skillName.toLowerCase());
        if (skills == null) {
            return null;
        }
        return skills.getFunction(funName, functionClazz);
    }

    @Nullable
    @Override
    public FunctionCollection getFunctions(String skillName) {
        return skillCollection.get(skillName.toLowerCase());
    }

    @Override
    public boolean hasFunction(String functionName) {
        return getFunction(functionName, SKFunction.class) != null;
    }

    @Override
    @CheckReturnValue
    public ReadOnlySkillCollection copy() {
        return new DefaultSkillCollection(skillCollection);
    }

    public DefaultSkillCollection addNativeFunction(SKFunction functionInstance) {
        // TODO is there any difference here?
        return addSemanticFunction(functionInstance);
    }

    public DefaultSkillCollection merge(DefaultSkillCollection in) {
        HashMap<String, FunctionCollection> clone = new HashMap<>(skillCollection);

        in.asMap()
                .entrySet()
                .forEach(
                        entry -> {
                            FunctionCollection existing = clone.get(entry.getKey().toLowerCase());
                            if (existing == null) {
                                clone.put(
                                        entry.getKey().toLowerCase(),
                                        new FunctionCollection(entry.getValue()));
                            } else {
                                clone.put(
                                        entry.getKey().toLowerCase(),
                                        existing.merge(new FunctionCollection(entry.getValue())));
                            }
                        });

        return new DefaultSkillCollection(clone);
    }

    @Override
    public Map<String, ReadOnlyFunctionCollection> asMap() {
        return Collections.unmodifiableMap(skillCollection);
    }

    @Override
    public FunctionCollection getAllFunctions() {
        return skillCollection.values().stream()
                .reduce(new FunctionCollection(""), FunctionCollection::merge);
    }
}
