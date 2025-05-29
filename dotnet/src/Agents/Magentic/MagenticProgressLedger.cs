// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// Structured response for the ledger evaluation.
/// </summary>
public sealed record MagenticProgressLedger(
    [property:Description("The name of who is selected to respond.")]
    string Name,
    [property:Description("Direction to who is responding that is specifically based on its capabilities and ALWAYS phrased in the 2nd person.")]
    string Instruction,
    [property:Description("The reason for selecting the agent.")]
    string Reason,
    [property:Description("Is the task completed?")]
    LedgerState IsTaskComplete,
    [property:Description("Is the task making progress, but not complete?")]
    LedgerState IsTaskProgressing,
    [property:Description("Is the task stuck in a loop?")]
    LedgerState IsTaskInLoop)
{
    private readonly static JsonSerializerOptions JsonOptions =
        new()
        {
            WriteIndented = true
        };

    /// <summary>
    /// Formats the ledger evaluation as a JSON string.
    /// </summary>
    public string ToJson() => JsonSerializer.Serialize(this, JsonOptions);
}

/// <summary>
/// Represents the evaluation state of a specific property in the progress ledger,
/// including the result and the reason for that result.
/// </summary>
public sealed record LedgerState(
    [property:Description("The result for the property being evaluated")]
    bool Result,
    [property:Description("The reason for the result")]
    string Reason)
{
    /// <summary>
    /// Implicitly converts a <see cref="LedgerState"/> to a <see cref="bool"/> by returning the <see cref="Result"/> property.
    /// </summary>
    /// <param name="state">The <see cref="LedgerState"/> instance to convert.</param>
    /// <returns>The <see cref="Result"/> value of the <see cref="LedgerState"/>.</returns>
    public static implicit operator bool(LedgerState state) => state.Result;
}
