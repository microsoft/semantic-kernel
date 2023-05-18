// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Access the collection in read-only mode, e.g. allow templates to search and execute functions.
/// </summary>
internal sealed class ReadOnlySkillCollection : IReadOnlySkillCollection
{
    private readonly ISkillCollection _skillCollection;

    public ReadOnlySkillCollection(ISkillCollection skillCollection) =>
        this._skillCollection = skillCollection;

    /// <inheritdoc/>
    public ISKFunction GetFunction(string functionName) =>
        this._skillCollection.GetFunction(functionName);

    /// <inheritdoc/>
    public ISKFunction GetFunction(string skillName, string functionName) =>
        this._skillCollection.GetFunction(skillName, functionName);

    /// <inheritdoc/>
    public bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction) =>
        this._skillCollection.TryGetFunction(functionName, out availableFunction);

    /// <inheritdoc/>
    public bool TryGetFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? availableFunction) =>
        this._skillCollection.TryGetFunction(skillName, functionName, out availableFunction);

    /// <inheritdoc/>
    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true) =>
        this._skillCollection.GetFunctionsView(includeSemantic, includeNative);
}
