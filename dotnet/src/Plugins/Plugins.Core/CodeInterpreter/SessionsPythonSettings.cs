// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Core.CodeInterpreter;

/// <summary>
/// Settings for a Python Sessions Plugin.
/// </summary>
public class SessionsPythonSettings
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
    public Uri Endpoint { get; set; }

    /// <summary>
    /// List of allowed domains to download from.
    /// </summary>
    public IEnumerable<string>? AllowedDomains { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether dangerous file upload operations are enabled.
    /// Default is <c>false</c>. Must be set to <c>true</c> along with configuring
    /// <see cref="AllowedUploadDirectories"/> to enable file uploads.
    /// </summary>
    [JsonIgnore]
    public bool EnableDangerousFileUploads { get; set; }

    /// <summary>
    /// Gets or sets the list of allowed local directories for file uploads.
    /// When <see cref="EnableDangerousFileUploads"/> is <c>true</c>, only files within these directories can be uploaded.
    /// If <c>null</c> or empty, file uploads are denied.
    /// </summary>
    [JsonIgnore]
    public IEnumerable<string>? AllowedUploadDirectories { get; set; }

    /// <summary>
    /// Gets or sets the list of allowed local directories for file downloads.
    /// If configured, files can only be downloaded to these directories.
    /// If <c>null</c> or empty, all paths are allowed (permissive by default).
    /// </summary>
    [JsonIgnore]
    public IEnumerable<string>? AllowedDownloadDirectories { get; set; }

    /// <summary>
    /// The session identifier.
    /// </summary>
    [JsonPropertyName("identifier")]
    public string SessionId { get; set; }

    /// <summary>
    /// Code input type.
    /// </summary>
    [JsonPropertyName("codeInputType")]
    public CodeInputTypeSetting CodeInputType { get; set; } = CodeInputTypeSetting.Inline;

    /// <summary>
    /// Code execution type.
    /// </summary>
    [JsonPropertyName("executionType")]
    public CodeExecutionTypeSetting CodeExecutionType { get; set; } = CodeExecutionTypeSetting.Synchronous;

    /// <summary>
    /// Timeout in seconds for the code execution.
    /// </summary>
    [JsonPropertyName("timeoutInSeconds")]
    public int TimeoutInSeconds { get; set; } = 100;

    /// <summary>
    /// Initializes a new instance of the <see cref="SessionsPythonSettings"/> class.
    /// </summary>
    /// <param name="sessionId">Session identifier.</param>
    /// <param name="endpoint">Azure Container Apps Endpoint.</param>
    [JsonConstructor]
    public SessionsPythonSettings(string sessionId, Uri endpoint)
    {
        this.SessionId = sessionId;
        this.Endpoint = endpoint;
    }

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
}
