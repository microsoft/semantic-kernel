// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;

/// <summary>
/// Represents a unique type of prompt, typically a semantic function, identified by the beginning of the prompt and the associated settings.
/// </summary>
[DebuggerDisplay("{PromptName}")]
public class PromptType
{
    /// <summary>
    /// Gets or sets the name of the prompt. Computed automatically or manually edited.
    /// </summary>
    public string PromptName { get; set; } = "";

    /// <summary>
    /// Sets the maximum number of distinct prompts to collect for this prompt type
    /// </summary>
    public int MaxInstanceNb { get; set; } = 10;

    /// <summary>
    /// recorded instances of the prompt type.
    /// </summary>
    public List<string> Instances { get; } = new();

    /// <summary>
    /// Identifying parameters of the prompt type, extracted from calls or manually edited.
    /// </summary>
    public PromptSignature Signature { get; set; } = new();

    /// <summary>
    /// While further instances of the prompt type are received, the start of the prompt may be adjusted to encompass the whole static part rather than just the first chars.
    /// </summary>
    public bool SignatureNeedsAdjusting { get; set; }
}
