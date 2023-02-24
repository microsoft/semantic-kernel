// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Memory.Storage;

/// <summary>
/// A struct containing properties for storage and retrieval of data.
/// </summary>
/// <typeparam name="TValue">The data <see cref="Type"/>.</typeparam>
public struct DataEntry<TValue> : IEquatable<DataEntry<TValue>>
{
    /// <summary>
    /// Creates an instance of a <see cref="DataEntry{TValue}"/>.
    /// </summary>
    /// <param name="key">The data key.</param>
    /// <param name="value">The data value.</param>
    /// <param name="timestamp">The data timestamp.</param>
    [JsonConstructor]
    public DataEntry(string key, TValue? value, DateTimeOffset? timestamp = null)
    {
        this.Key = key;
        this.Value = value;
        this.Timestamp = timestamp;
    }

    /// <summary>
    /// Gets the key of the data.
    /// </summary>
    [JsonPropertyName("key")]
    public readonly string Key { get; }

    /// <summary>
    /// Gets the value of the data.
    /// </summary>
    [JsonPropertyName("value")]
    public TValue? Value { get; set; }

    /// <summary>
    /// Gets the timestamp of the data.
    /// </summary>
    [JsonPropertyName("timestamp")]
    public DateTimeOffset? Timestamp { get; set; } = null;

    /// <summary>
    /// Gets the data value type.
    /// </summary>
    [JsonIgnore]
    public Type ValueType => typeof(TValue);

    /// <summary>
    /// <c>true</c> if the data has a value.
    /// </summary>
    [JsonIgnore]
    public bool HasValue => (this.Value != null);

    /// <summary>
    /// <c>true</c> if the data has a timestamp.
    /// </summary>
    [JsonIgnore]
    public bool HasTimestamp => this.Timestamp.HasValue;

    /// <summary>
    /// The <see cref="Value"/> as a <see cref="string"/>.
    /// </summary>
    [JsonIgnore]
    public string? ValueString
    {
        get
        {
            if (this.ValueType == typeof(string))
            {
                return this.Value?.ToString();
            }

            if (this.Value != null)
            {
                return JsonSerializer.Serialize(this.Value);
            }

            return null;
        }
    }

    /// <summary>
    /// Compares two objects for equality.
    /// </summary>
    /// <param name="other">The <see cref="DataEntry{TValue}"/> to compare.</param>
    /// <returns><c>true</c> if the specified object is equal to the current object; otherwise, <c>false</c>.</returns>
    public bool Equals(DataEntry<TValue> other)
    {
        return (other != null)
               && (this.Key == other.Key)
               && (this.Value?.Equals(other.Value) == true)
               && (this.Timestamp == other.Timestamp);
    }

    /// <summary>
    /// Determines whether two object instances are equal.
    /// </summary>
    /// <param name="obj">The object to compare with the current object.</param>
    /// <returns><c>true</c> if the specified object is equal to the current object; otherwise, <c>false</c>.</returns>
    public override bool Equals(object obj)
    {
        return (obj is DataEntry<TValue> other) && this.Equals(other);
    }

    /// <summary>
    /// Serves as the default hash function.
    /// </summary>
    /// <returns>A hash code for the current object.</returns>
    public override int GetHashCode()
    {
        return HashCode.Combine(this.Key, this.Value, this.Timestamp);
    }

    /// <summary>
    /// Returns a string that represents the current object.
    /// </summary>
    /// <returns>Returns a string that represents the current object.</returns>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Parses a <see cref="DataEntry{TValue}"/> object from a serialized JSON string.
    /// </summary>
    /// <param name="json">The source JSON string.</param>
    /// <param name="entry">The resulting <see cref="DataEntry{TValue}"/>, or null if empty.</param>
    /// <returns>true if parsing is successful, false otherwise.</returns>
    [SuppressMessage("Design", "CA1000:Do not declare static members on generic types", Justification = "Parse type from string.")]
    [SuppressMessage("Design", "CA1031:Modify to catch a more specific allowed exception type, or rethrow exception",
        Justification = "Does not throw an exception by design.")]
    public static bool TryParse(string json, [NotNullWhen(true)] out DataEntry<TValue>? entry)
    {
        try
        {
            entry = JsonSerializer.Deserialize<DataEntry<TValue>>(json);
            return true;
        }
        catch
        {
            entry = default;
            return false;
        }
    }

    /// <summary>
    /// Compares two embeddings for equality.
    /// </summary>
    /// <param name="left">The left <see cref="DataEntry{TValue}"/>.</param>
    /// <param name="right">The right <see cref="DataEntry{TValue}"/>.</param>
    /// <returns><c>true</c> if the embeddings contain identical data.</returns>
    public static bool operator ==(DataEntry<TValue> left, DataEntry<TValue> right)
    {
        return left.Equals(right);
    }

    /// <summary>
    /// Compares two embeddings for inequality.
    /// </summary>
    /// <param name="left">The left <see cref="DataEntry{TValue}"/>.</param>
    /// <param name="right">The right <see cref="DataEntry{TValue}"/>.</param>
    /// <returns><c>true</c> if the embeddings do not contain identical data.</returns>
    public static bool operator !=(DataEntry<TValue> left, DataEntry<TValue> right)
    {
        return !(left == right);
    }
}

/// <summary>
/// Provides a collection of static methods for creating, manipulating, and otherwise operating on generic <see cref="DataEntry{TValue}"/> objects.
/// </summary>
public static class DataEntry
{
    /// <summary>
    /// Creates a new <see cref="DataEntry{TValue}"/> object.
    /// </summary>
    /// <typeparam name="TValue">The data value <see cref="Type"/>.</typeparam>
    /// <param name="key">The storage key for the data.</param>
    /// <param name="value">The data value.</param>
    /// <param name="timestamp">The data timestamp.</param>
    /// <returns>A <see cref="DataEntry{TValue}"/> object.</returns>
    public static DataEntry<TValue> Create<TValue>(string key, TValue? value, DateTimeOffset? timestamp = null)
    {
        Verify.NotEmpty(key, "Data entry key cannot be NULL");

        return new DataEntry<TValue>(key, value, timestamp);
    }

    /// <summary>
    /// Creates a new <see cref="DataEntry{TValue}"/> object from a string value.
    /// </summary>
    /// <typeparam name="TValue">The data value <see cref="Type"/>.</typeparam>
    /// <param name="key">The storage key for the data.</param>
    /// <param name="value">The data value.</param>
    /// <param name="timestamp">The data timestamp.</param>
    /// <returns>A <see cref="DataEntry{TValue}"/> object.</returns>
    public static DataEntry<TValue> Create<TValue>(string key, string value, DateTimeOffset? timestamp = null)
    {
        Verify.NotEmpty(key, "Data entry key cannot be NULL");

        TValue? valueObj = ParseValueAs<TValue>(value);
        return new DataEntry<TValue>(key, valueObj, timestamp);
    }

    /// <summary>
    /// Parses a <see cref="DataEntry{TValue}"/> object from a serialized JSON string.
    /// </summary>
    /// <typeparam name="TValue">The data value <see cref="Type"/>.</typeparam>
    /// <param name="json">A JSON serialized string representing a <see cref="DataEntry{TValue}"/>.</param>
    /// <param name="entry">Receives a <see cref="DataEntry{TValue}"/> object if successfully parsed. Null otherwise.</param>
    /// <returns><c>true</c> if parsing is successful; <c>false</c> otherwise</returns>
    public static bool TryParse<TValue>(string json, [NotNullWhen(true)] out DataEntry<TValue>? entry)
    {
        return DataEntry<TValue>.TryParse(json, out entry);
    }

    #region private ================================================================================

    [SuppressMessage("Design", "CA1031:Modify to catch a more specific allowed exception type, or rethrow exception",
        Justification = "Does not throw an exception by design.")]
    internal static TCastTo? ParseValueAs<TCastTo>(string? value)
    {
        if (!string.IsNullOrWhiteSpace(value))
        {
            if (typeof(TCastTo) == typeof(string))
            {
                // Force cast (we already know this is type string)
                return (TCastTo)Convert.ChangeType(value, typeof(TCastTo), CultureInfo.InvariantCulture);
            }

            return JsonSerializer.Deserialize<TCastTo>(value);
        }

        return default;
    }

    // TODO: method never used
    private static DataEntry<TCastTo>? As<TCastTo, TCastFrom>(DataEntry<TCastFrom> data)
    {
        if (data == null)
        {
            return default;
        }

        if (data.ValueType == typeof(TCastTo))
        {
            // To and From types are the same. Just cast to satisfy the compiler.
            return (DataEntry<TCastTo>)Convert.ChangeType(data, typeof(DataEntry<TCastTo>), CultureInfo.InvariantCulture);
        }

        if (!data.HasValue)
        {
            // Data has no 'value' set. Create a new DataEntry with the desired type, and copy over the other properties.
            return new DataEntry<TCastTo>(data.Key, default, data.Timestamp);
        }

        if (data.ValueType == typeof(string))
        {
            // Convert from a string value data to another type. Try to deserialize value.
            TCastTo? destinationValue = ParseValueAs<TCastTo>(data.ValueString);
            if (destinationValue == null)
            {
                // Cast failed. Return null DataEntry.
                return default;
            }

            return new DataEntry<TCastTo>(data.Key, destinationValue, data.Timestamp);
        }

        if (typeof(TCastTo) == typeof(string))
        {
            // Convert from another value type to string. Use serialized value from ValueString.
            // TODO: entry is never used
            var entry = new DataEntry<string>(data.Key, data.ValueString, data.Timestamp);
            return (DataEntry<TCastTo>)Convert.ChangeType(data, typeof(DataEntry<TCastTo>), CultureInfo.InvariantCulture);
        }

        // Converting between two non-string value types... see if there's a cast available
        try
        {
            TCastTo destValue = (TCastTo)Convert.ChangeType(data.Value, typeof(TCastTo), CultureInfo.InvariantCulture);
            return new DataEntry<TCastTo>(data.Key, destValue, data.Timestamp);
        }
        catch (InvalidCastException)
        {
            // Cast failed. Return null DataEntry.
            return default;
        }
    }

    #endregion
}
