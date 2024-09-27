// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.orchestration.SKFunction;
import java.util.Collections;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;
import javax.annotation.CheckReturnValue;
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

    public DefaultSkillCollection addSemanticFunction(SKFunction functionInstance) {
        FunctionCollection existingFunctionCollection;
        if (!skillCollection.containsKey(functionInstance.getSkillName())) {
            existingFunctionCollection = new FunctionCollection(functionInstance.getSkillName());
            skillCollection.put(functionInstance.getSkillName(), existingFunctionCollection);
        } else {
            existingFunctionCollection = skillCollection.get(functionInstance.getSkillName());
        }

        existingFunctionCollection.put(functionInstance.getName(), functionInstance);

        return this;
    }

    @Override
    @Nullable
    public <T extends SKFunction<?>> T getFunction(
            String funName, @Nullable Class<T> functionClazz) {
        return getFunction(GlobalSkill, funName, functionClazz);
    }

    @Override
    @Nullable
    public <T extends SKFunction<?>> T getFunction(
            String skillName, String funName, @Nullable Class<T> functionClazz) {
        FunctionCollection skills = skillCollection.get(skillName.toLowerCase(Locale.ROOT));
        if (skills == null) {
            return null;
        }
        return skills.getFunction(funName, functionClazz);
    }

    @Nullable
    @Override
    public FunctionCollection getFunctions(String skillName) {
        return skillCollection.get(skillName.toLowerCase(Locale.ROOT));
    }

    @Override
    public boolean hasFunction(String functionName) {
        return getFunction(functionName, SKFunction.class) != null;
    }

    @Override
    public boolean hasFunction(String skillName, String functionName) {
        FunctionCollection skills = skillCollection.get(skillName.toLowerCase(Locale.ROOT));
        if (skills == null) {
            return false;
        }
        return skills.getFunction(functionName) != null;
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

    public DefaultSkillCollection merge(ReadOnlySkillCollection in) {
        in.asMap()
                .entrySet()
                .forEach(
                        entry -> {
                            FunctionCollection existing =
                                    skillCollection.get(entry.getKey().toLowerCase(Locale.ROOT));
                            if (existing == null) {
                                skillCollection.put(
                                        entry.getKey().toLowerCase(Locale.ROOT),
                                        new FunctionCollection(entry.getValue()));
                            } else {
                                existing.merge(new FunctionCollection(entry.getValue()));
                            }
                        });
        return this;
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
