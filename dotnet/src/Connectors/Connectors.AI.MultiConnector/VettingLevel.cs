namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the vetting level of a connector against a prompt type.
/// </summary>
public enum VettingLevel
{
    Invalid = -1,
    None = 0,
    Oracle = 3,
    OracleVaried = 4 // Oracle varied means distinct prompts were used for vetting tests.
}