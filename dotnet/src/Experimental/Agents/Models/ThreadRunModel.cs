// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

/// <summary>
/// Represents an execution run on a thread.
/// </summary>
internal sealed class ThreadRunModel
{
    /// <summary>
    /// Identifier, which can be referenced in API endpoints.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Unix timestamp (in seconds) for when the run was created.
    /// </summary>
    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    /// <summary>
    /// ID of the agent used for execution of this run.
    /// </summary>
    [JsonPropertyName("agent_id")]
    public string AgentId { get; set; } = string.Empty;

    /// <summary>
    /// ID of the thread that was executed on as a part of this run.
    /// </summary>
    [JsonPropertyName("thread_id")]
    public string ThreadId { get; set; } = string.Empty;

    /// <summary>
    /// The status of the run, which can be one of:
    /// queued, in_progress, requires_action, cancelling, cancelled, failed, completed, or expired.
    /// </summary>
    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    /// <summary>
    /// Unix timestamp (in seconds) for when the run was started.
    /// </summary>
    [JsonPropertyName("started_at")]
    public long? StartedAt { get; set; }

    /// <summary>
    /// Unix timestamp (in seconds) for when the run will expire.
    /// </summary>
    [JsonPropertyName("expires_at")]
    public long? ExpiresAt { get; set; }

    /// <summary>
    /// Unix timestamp (in seconds) for when the run was cancelled.
    /// </summary>
    [JsonPropertyName("cancelled_at")]
    public long? CancelledAt { get; set; }

    /// <summary>
    /// Unix timestamp (in seconds) for when the run failed.
    /// </summary>
    [JsonPropertyName("failed_at")]
    public long? FailedAt { get; set; }

    /// <summary>
    /// Unix timestamp (in seconds) for when the run was completed.
    /// </summary>
    [JsonPropertyName("completed_at")]
    public long? CompletedAt { get; set; }

    /// <summary>
    /// The last error associated with this run. Will be null if there are no errors.
    /// </summary>
    [JsonPropertyName("last_error")]
    public ErrorModel? LastError { get; set; }

    /// <summary>
    /// The model that the agent used for this run.
    /// </summary>
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    /// <summary>
    /// The instructions that the agent used for this run.
    /// </summary>
    [JsonPropertyName("instructions")]
    public string Instructions { get; set; } = string.Empty;

    /// <summary>
    /// The list of tools that the agent used for this run.
    /// </summary>
    [JsonPropertyName("tools")]
    public List<ToolModel> Tools { get; set; } = new List<ToolModel>();

    /// <summary>
    /// The list of File IDs the agent used for this run.
    /// </summary>
    [JsonPropertyName("file_ids")]
    public List<string> FileIds { get; set; } = new List<string>();

    /// <summary>
    /// Set of 16 key-value pairs that can be attached to an object.
    /// This can be useful for storing additional information about the
    /// object in a structured format. Keys can be a maximum of 64
    /// characters long and values can be a maximum of 512 characters long.
    /// </summary>
    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = new Dictionary<string, object>();

    /// <summary>
    /// Run error information.
    /// </summary>
    public sealed class ErrorModel
    {
        /// <summary>
        /// Error code.
        /// </summary>
        [JsonPropertyName("code")]
        public string Code { get; set; } = string.Empty;

        /// <summary>
        /// Error message.
        /// </summary>
        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;
    }
}
