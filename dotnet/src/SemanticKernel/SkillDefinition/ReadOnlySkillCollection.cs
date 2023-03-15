// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Access the collection in read-only mode, e.g. allow templates to search and execute functions.
/// </summary>
internal class ReadOnlySkillCollection : IReadOnlySkillCollection
{
    private readonly ISkillCollection _skillCollection;

    public ReadOnlySkillCollection(ISkillCollection skillCollection)
    {
        this._skillCollection = skillCollection;
    }

    /// <inheritdoc/>
    public bool HasFunction(string skillName, string functionName)
    {
        return this._skillCollection.HasFunction(skillName, functionName);
    }

    /// <inheritdoc/>
    public bool HasFunction(string functionName)
    {
        return this._skillCollection.HasFunction(functionName);
    }

    /// <inheritdoc/>
    public bool HasSemanticFunction(string skillName, string functionName)
    {
        return this._skillCollection.HasSemanticFunction(skillName, functionName);
    }

    /// <inheritdoc/>
    public bool HasNativeFunction(string skillName, string functionName)
    {
        return this._skillCollection.HasNativeFunction(skillName, functionName);
    }

    /// <inheritdoc/>
    public bool HasNativeFunction(string functionName)
    {
        return this._skillCollection.HasNativeFunction(functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName)
    {
        return this._skillCollection.GetFunction(functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetFunction(string skillName, string functionName)
    {
        return this._skillCollection.GetFunction(skillName, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string functionName)
    {
        return this._skillCollection.GetSemanticFunction(functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string skillName, string functionName)
    {
        return this._skillCollection.GetSemanticFunction(skillName, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string skillName, string functionName)
    {
        return this._skillCollection.GetNativeFunction(skillName, functionName);
    }

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string functionName)
    {
        return this._skillCollection.GetNativeFunction(functionName);
    }

    /// <inheritdoc/>
    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true)
    {
        return this._skillCollection.GetFunctionsView(includeSemantic, includeNative);
    }
}
