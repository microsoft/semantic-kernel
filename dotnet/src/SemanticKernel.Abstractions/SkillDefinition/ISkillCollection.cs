// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Skill collection interface.
/// </summary>
[SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix")]
public interface ISkillCollection : IReadOnlySkillCollection
{
    /// <summary>
    /// Add a function to the collection
    /// </summary>
    /// <param name="functionInstance">Function delegate</param>
    /// <returns>Self instance</returns>
    ISkillCollection AddFunction(ISKFunction functionInstance);
}
