// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;

/// <summary>
/// Represents the result of a Python code execution.
/// </summary>
public sealed class SessionsPythonCodeExecutionResult
{
    /// <summary>
    /// Gets or sets the status of the execution (e.g., Succeeded, Failed).
    /// </summary>
    [JsonPropertyName("status")]
    public required string Status { get; set; }

    /// <summary>
    /// Gets or sets the detailed result of the execution.
    /// </summary>
    [JsonPropertyName("result")]
    public ExecutionDetails? Result { get; set; }

    /// <summary>
    /// Returns a string representation of the execution result.
    /// </summary>
    public override string ToString()
    {
        return JsonSerializer.Serialize(new
        {
            status = this.Status,
            result = this.Result?.ExecutionResult,
            stdOut = this.Result?.StdOut,
            stdErr = this.Result?.StdErr
        });
    }

    /// <summary>
    /// Represents the detailed result of a Python code execution.
    /// </summary>
    public sealed class ExecutionDetails
    {
        /// <summary>
        /// Gets or sets the standard output (stdout) of the code execution.
        /// </summary>
        [JsonPropertyName("stdout")]
        public string? StdOut { get; set; }

        /// <summary>
        /// Gets or sets the standard error (stderr) of the code execution.
        /// </summary>
        [JsonPropertyName("stderr")]
        public string? StdErr { get; set; }

        /// <summary>
        /// Gets or sets the result of the code execution.
        /// </summary>
        [JsonPropertyName("executionResult")]
        public string? ExecutionResult { get; set; }
    }
}
