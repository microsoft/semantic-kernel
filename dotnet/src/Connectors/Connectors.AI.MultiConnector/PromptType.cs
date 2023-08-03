using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents a unique type of prompt, typically a semantic function, identified by the beginning of the prompt and the associated settings.
/// </summary>
public class PromptType
{
    /// <summary>
    /// Gets or sets the name of the prompt. Computed automatically or manually edited.
    /// </summary>
    public string PromptName { get; set; } = "";

    /// <summary>
    /// recorded instances of the prompt type.
    /// </summary>
    public List<string> Instances { get; } = new();

    /// <summary>
    /// Identifying parameters of the prompt type, extracted from calls or manually edited.
    /// </summary>
    public PromptSignature Signature { get; set; } = new();
}