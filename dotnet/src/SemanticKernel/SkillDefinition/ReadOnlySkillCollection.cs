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
    public bool TryGetFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this._skillCollection.TryGetFunction(functionName, out functionInstance);

    /// <inheritdoc/>
    public bool TryGetFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this._skillCollection.TryGetFunction(skillName, functionName, out functionInstance);

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string functionName) =>
        this._skillCollection.GetSemanticFunction(functionName);

    /// <inheritdoc/>
    public ISKFunction GetSemanticFunction(string skillName, string functionName) =>
        this._skillCollection.GetSemanticFunction(skillName, functionName);

    /// <inheritdoc/>
    public bool TryGetSemanticFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this._skillCollection.TryGetSemanticFunction(functionName, out functionInstance);

    /// <inheritdoc/>
    public bool TryGetSemanticFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this._skillCollection.TryGetSemanticFunction(skillName, functionName, out functionInstance);

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string functionName) =>
        this._skillCollection.GetNativeFunction(functionName);

    /// <inheritdoc/>
    public ISKFunction GetNativeFunction(string skillName, string functionName) =>
        this._skillCollection.GetNativeFunction(skillName, functionName);

    /// <inheritdoc/>
    public bool TryGetNativeFunction(string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this._skillCollection.TryGetNativeFunction(functionName, out functionInstance);

    /// <inheritdoc/>
    public bool TryGetNativeFunction(string skillName, string functionName, [NotNullWhen(true)] out ISKFunction? functionInstance) =>
        this._skillCollection.TryGetNativeFunction(skillName, functionName, out functionInstance);

    /// <inheritdoc/>
    public FunctionsView GetFunctionsView(bool includeSemantic = true, bool includeNative = true) =>
        this._skillCollection.GetFunctionsView(includeSemantic, includeNative);
}
