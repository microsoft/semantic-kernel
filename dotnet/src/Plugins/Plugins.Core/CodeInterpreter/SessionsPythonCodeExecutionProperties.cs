// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using static Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter.SessionsPythonSettings;

namespace Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;

internal sealed class SessionsPythonCodeExecutionProperties
{
    /// <summary>
    /// The session identifier.
    /// </summary>
    [JsonPropertyName("identifier")]
    public string Identifier { get; }

    /// <summary>
    /// Code input type.
    /// </summary>
    [JsonPropertyName("codeInputType")]
    public CodeInputTypeSetting CodeInputType { get; } = CodeInputTypeSetting.Inline;

    /// <summary>
    /// Code execution type.
    /// </summary>
    [JsonPropertyName("executionType")]
    public CodeExecutionTypeSetting CodeExecutionType { get; } = CodeExecutionTypeSetting.Synchronous;

    /// <summary>
    /// Timeout in seconds for the code execution.
    /// </summary>
    [JsonPropertyName("timeoutInSeconds")]
    public int TimeoutInSeconds { get; } = 100;

    /// <summary>
    /// The Python code to execute.
    /// </summary>
    [JsonPropertyName("pythonCode")]
    public string? PythonCode { get; }

    public SessionsPythonCodeExecutionProperties(SessionsPythonSettings settings, string pythonCode)
    {
        this.Identifier = settings.SessionId;
        this.PythonCode = pythonCode;
        this.TimeoutInSeconds = settings.TimeoutInSeconds;
        this.CodeInputType = settings.CodeInputType;
        this.CodeExecutionType = settings.CodeExecutionType;
    }
}
