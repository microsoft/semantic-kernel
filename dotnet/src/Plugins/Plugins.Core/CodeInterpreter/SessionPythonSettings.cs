// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;

/// <summary>
/// Settings for a Python session.
/// </summary>
public class SessionPythonSettings
{
    /// <summary>
    /// Determines if the input should be sanitized.
    /// </summary>
    [JsonIgnore]
    public bool SanitizeInput { get; set; }

    /// <summary>
    /// The target endpoint.
    /// </summary>
    [JsonIgnore]
    public Uri? Endpoint { get; init; }

    /// <summary>
    /// The session identifier.
    /// </summary>
    [JsonPropertyName("identifier")]
    public string? SessionId { get; init; }

    /// <summary>
    /// Code input type.
    /// </summary>
    [JsonPropertyName("codeInputType")]
    public CodeInputTypeSetting CodeInputType { get; set; }

    /// <summary>
    /// Code execution type.
    /// </summary>
    [JsonPropertyName("executionType")]
    public CodeExecutionTypeSetting CodeExecutionType { get; set; }

    /// <summary>
    /// Timeout in seconds for the code execution.
    /// </summary>
    [JsonPropertyName("timeoutInSeconds")]
    public int TimeoutInSeconds { get; set; } = 100;

    /// <summary>
    /// The Python code to execute.
    /// </summary>
    [JsonPropertyName("pythonCode")]
    public string? PythonCode { get; set; }

    /// <summary>
    /// Code input type.
    /// </summary>
    [Description("Code input type.")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum CodeInputTypeSetting
    {
        /// <summary>
        /// Code is provided as a inline string.
        /// </summary>
        [Description("Code is provided as a inline string.")]
        [JsonPropertyName("inline")]
        Inline
    }

    /// <summary>
    /// Code input type.
    /// </summary>
    [Description("Code input type.")]
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum CodeExecutionTypeSetting
    {
        /// <summary>
        /// Code is provided as a inline string.
        /// </summary>
        [Description("Code is provided as a inline string.")]
        [JsonPropertyName("synchronous")]
        Synchronous
    }

    internal SessionPythonSettings CloneForRequest(string pythonCode)
    {
        return new SessionPythonSettings
        {
            SanitizeInput = this.SanitizeInput,
            SessionId = this.SessionId,
            CodeInputType = this.CodeInputType,
            CodeExecutionType = this.CodeExecutionType,
            TimeoutInSeconds = this.TimeoutInSeconds,
            PythonCode = pythonCode
        };
    }
}
