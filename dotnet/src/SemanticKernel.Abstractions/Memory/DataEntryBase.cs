// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A base class for data entries.
/// </summary>
public class DataEntryBase
{
    /// <summary>
    /// Creates an instance of a <see cref="DataEntryBase"/>.
    /// </summary>
    /// <param name="key">The data key.</param>
    /// <param name="timestamp">The data timestamp.</param>
    [JsonConstructor]
    public DataEntryBase(string? key = null, DateTimeOffset? timestamp = null)
    {
        this.Key = key ?? string.Empty;
        this.Timestamp = timestamp;
    }

    /// <summary>
    /// Gets the key of the data.
    /// </summary>
    [JsonPropertyName("key")]
    public string Key { get; set; }

    /// <summary>
    /// Gets the timestamp of the data.
    /// </summary>
    [JsonPropertyName("timestamp")]
    public DateTimeOffset? Timestamp { get; set; }

    /// <summary>
    /// <c>true</c> if the data has a timestamp.
    /// </summary>
    [JsonIgnore]
    public bool HasTimestamp => this.Timestamp.HasValue;
}
