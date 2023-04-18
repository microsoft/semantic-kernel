// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Skill collection interface.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1710:Identifiers should have correct suffix", Justification = "It is a collection")]
[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix", Justification = "It is a collection")]
public interface ISkillCollection : IReadOnlySkillCollection
{
    /// <summary>
    /// Readonly only access into the collection
    /// </summary>
    IReadOnlySkillCollection ReadOnlySkillCollection { get; }

    /// <summary>
    /// Add a semantic function to the collection
    /// </summary>
    /// <param name="functionInstance">Function delegate</param>
    /// <returns>Self instance</returns>
    ISkillCollection AddSemanticFunction(ISKFunction functionInstance);

    /// <summary>
    /// Add a native function to the collection
    /// </summary>
    /// <param name="functionInstance">Wrapped function delegate</param>
    /// <returns>Self instance</returns>
    ISkillCollection AddNativeFunction(ISKFunction functionInstance);
}
