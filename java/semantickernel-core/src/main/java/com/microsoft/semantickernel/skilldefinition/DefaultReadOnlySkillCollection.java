// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition; // Copyright (c) Microsoft. All rights
// reserved.

import com.microsoft.semantickernel.orchestration.SKFunction;

import java.util.Collections;
import java.util.HashMap;
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
public class DefaultReadOnlySkillCollection implements ReadOnlySkillCollection {

    public static class Builder implements ReadOnlySkillCollection.Builder {
        @Override
        public ReadOnlySkillCollection build() {
            return new DefaultReadOnlySkillCollection();
        }
    }

    private final Map<String, ReadOnlyFunctionCollection> skillCollection;

    public DefaultReadOnlySkillCollection(Map<String, ReadOnlyFunctionCollection> skillCollection) {
        this.skillCollection =
                Collections.unmodifiableMap(
                        skillCollection.entrySet().stream()
                                .collect(
                                        Collectors.toMap(
                                                Map.Entry::getKey, it -> it.getValue().copy())));
    }

    public DefaultReadOnlySkillCollection() {
        this.skillCollection = Collections.unmodifiableMap(new HashMap<>());
    }

    @Override
    @CheckReturnValue
    public ReadOnlySkillCollection addSemanticFunction(SKFunction functionInstance) {
        ReadOnlyFunctionCollection existingFunctionCollection;
        if (!skillCollection.containsKey(functionInstance.getSkillName().toLowerCase())) {
            existingFunctionCollection =
                    new ReadOnlyFunctionCollection(functionInstance.getSkillName().toLowerCase());
        } else {
            existingFunctionCollection =
                    skillCollection.get(functionInstance.getSkillName().toLowerCase());
        }

        existingFunctionCollection =
                existingFunctionCollection.put(
                        functionInstance.getName().toLowerCase(), functionInstance);

        HashMap<String, ReadOnlyFunctionCollection> clonedSkillCollection =
                new HashMap<>(skillCollection);

        clonedSkillCollection.put(
                functionInstance.getSkillName().toLowerCase(), existingFunctionCollection);

        return new DefaultReadOnlySkillCollection(clonedSkillCollection);
    }

    @Override
    @Nullable
    public <T extends SKFunction<?, ?>> T getFunction(String funName, Class<T> functionClazz) {
        return getFunction(GlobalSkill, funName, functionClazz);
    }

    @Override
    @Nullable
    public <T extends SKFunction<?, ?>> T getFunction(
            String skillName, String funName, Class<T> functionClazz) {
        ReadOnlyFunctionCollection skills = skillCollection.get(skillName.toLowerCase());
        if (skills == null) {
            return null;
        }
        return skills.getFunction(funName, functionClazz);
    }

    @Nullable
    @Override
    public ReadOnlyFunctionCollection getFunctions(String skillName) {
        return skillCollection.get(skillName.toLowerCase());
    }

    @Override
    @CheckReturnValue
    public ReadOnlySkillCollection copy() {
        return new DefaultReadOnlySkillCollection(skillCollection);
    }

    @Override
    public ReadOnlySkillCollection addNativeFunction(SKFunction functionInstance) {
        // TODO is there any difference here?
        return addSemanticFunction(functionInstance);
    }

    @Override
    public ReadOnlySkillCollection merge(ReadOnlySkillCollection in) {
        HashMap<String, ReadOnlyFunctionCollection> clone = new HashMap<>(skillCollection);

        in.asMap()
                .entrySet()
                .forEach(
                        entry -> {
                            ReadOnlyFunctionCollection existing =
                                    clone.get(entry.getKey().toLowerCase());
                            if (existing == null) {
                                clone.put(entry.getKey().toLowerCase(), entry.getValue());
                            } else {
                                clone.put(
                                        entry.getKey().toLowerCase(),
                                        existing.merge(entry.getValue()));
                            }
                        });

        return new DefaultReadOnlySkillCollection(clone);
    }

    @Override
    public Map<String, ReadOnlyFunctionCollection> asMap() {
        return Collections.unmodifiableMap(skillCollection);
    }

    @Override
    public ReadOnlyFunctionCollection getAllFunctions() {
        return skillCollection.values().stream()
                .reduce(new ReadOnlyFunctionCollection(""), ReadOnlyFunctionCollection::merge);
    }
    /*
    internal const string GlobalSkill = "_GLOBAL_FUNCTIONS_";

    /// <inheritdoc/>
    public IReadOnlySkillCollection ReadOnlySkillCollection { get; private set; }

    public SkillCollection(ILogger? log = null)
    {
        if (log != null) { this._log = log; }

        this.ReadOnlySkillCollection = new ReadOnlySkillCollection(this);

        // Important: names are case insensitive
        this._skillCollection = new(StringComparer.InvariantCultureIgnoreCase);
    }

    /// <inheritdoc/>
    public ISkillCollection AddSemanticFunction(ISKFunction functionInstance)
    {
        if (!this._skillCollection.ContainsKey(functionInstance.SkillName))
        {
            // Important: names are case insensitive
            this._skillCollection[functionInstance.SkillName] = new(StringComparer.InvariantCultureIgnoreCase);
        }

        this._skillCollection[functionInstance.SkillName][functionInstance.Name] = functionInstance;

        return this;
    }

    /// <inheritdoc/>
    public ISkillCollection AddNativeFunction(ISKFunction functionInstance)
    {
        Verify.NotNull(functionInstance, "The function is NULL");
        if (!this._skillCollection.ContainsKey(functionInstance.SkillName))
        {
            // Important: names are case insensitive
            this._skillCollection[functionInstance.SkillName] = new(StringComparer.InvariantCultureIgnoreCase);
        }

        this._skillCollection[functionInstance.SkillName][functionInstance.Name] = functionInstance;
        return this;
    }

    /// <inheritdoc/>
    public bool HasFunction(string skillName, string functionName)
    {
        return this._skillCollection.ContainsKey(skillName) &&
               this._skillCollection[skillName].ContainsKey(functionName);
    }

    /// <inheritdoc/>
    public bool HasFunction(string functionName)
    {
        return this._skillCollection.ContainsKey(GlobalSkill) &&
               this._skillCollection[GlobalSkill].ContainsKey(functionName);
    }

    /// <inheritdoc/>
    public bool HasSemanticFunction(string skillName, string functionName)
    {
        return this.HasFunction(skillName, functionName)
               && this._skillCollection[skillName][functionName].IsSemantic;
    }

    /// <inheritdoc/>
    public bool HasNativeFunction(string skillName, string functionName)
    {
        return this.HasFunction(skillName, functionName)
               && !this._skillCollection[skillName][functionName].IsSemantic;
    }

    /// <inheritdoc/>
    public bool HasNativeFunction(string functionName)
    {
        return this.HasNativeFunction(GlobalSkill, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName)
    {
        return this.GetFunction(GlobalSkill, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string skillName, string functionName)
    {
        if (this.HasFunction(skillName, functionName))
        {
            return this._skillCollection[skillName][functionName];
        }

        this._log.LogError("Function not available: skill:{0} function:{1}", skillName, functionName);
        throw new KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            $"Function not available {skillName}.{functionName}");
    }

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string functionName)
    {
        return this.GetSemanticFunction(GlobalSkill, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string skillName, string functionName)
    {
        if (this.HasSemanticFunction(skillName, functionName))
        {
            return this._skillCollection[skillName][functionName];
        }

        this._log.LogError("Function not available: skill:{0} function:{1}", skillName, functionName);
        throw new KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            $"Function not available {skillName}.{functionName}");
    }

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string skillName, string functionName)
    {
        if (this.HasNativeFunction(skillName, functionName))
        {
            return this._skillCollection[skillName][functionName];
        }

        this._log.LogError("Function not available: skill:{0} function:{1}", skillName, functionName);
        throw new KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            $"Function not available {skillName}.{functionName}");
    }

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string functionName)
    {
        return this.GetNativeFunction(GlobalSkill, functionName);
    }

    /// <inheritdoc/>
    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true)
    {
        var result = new FunctionsView();

        if (includeSemantic)
        {
            foreach (var skill in this._skillCollection)
            {
                foreach (KeyValuePair<string, ISKFunction> f in skill.Value)
                {
                    if (f.Value.IsSemantic) { result.AddFunction(f.Value.Describe()); }
                }
            }
        }

        if (!includeNative) { return result; }

        foreach (var skill in this._skillCollection)
        {
            foreach (KeyValuePair<string, ISKFunction> f in skill.Value)
            {
                if (!f.Value.IsSemantic) { result.AddFunction(f.Value.Describe()); }
            }
        }

        return result;
    }

    #region private ================================================================================

    private readonly ILogger _log = NullLogger.Instance;

    private readonly ConcurrentDictionary<string, ConcurrentDictionary<string, ISKFunction>> _skillCollection;

    #endregion

     */
}
