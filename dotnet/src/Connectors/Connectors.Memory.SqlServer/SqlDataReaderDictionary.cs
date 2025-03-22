// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// This class is used to provide a dictionary-like interface to a <see cref="SqlDataReader"/>.
/// The goal is to avoid the need of allocating a new dictionary for each row read from the database.
/// </summary>
internal sealed class SqlDataReaderDictionary(SqlDataReader sqlDataReader, IReadOnlyList<VectorStoreRecordVectorPropertyModel> vectorProperties)
    : IDictionary<string, object?>
{
    // This field will get instantiated lazily, only if needed by a custom mapper.
    private Dictionary<string, object?>? _dictionary;

    private object? Unwrap(string storageName, object? value)
    {
        // Let's make sure our users don't need to learn what DBNull is.
        if (value is DBNull)
        {
            return null;
        }

        // If the value is a vector, we need to deserialize it.
        if (vectorProperties.Count > 0 && value is string text)
        {
            for (int i = 0; i < vectorProperties.Count; i++)
            {
                if (string.Equals(storageName, vectorProperties[i].StorageName, StringComparison.Ordinal))
                {
                    try
                    {
                        return JsonSerializer.Deserialize<ReadOnlyMemory<float>>(text);
                    }
                    catch (JsonException)
                    {
                        // This may fail if the user has stored a non-float array in the database
                        // (or serialized it in a different way).
                        // We need to return the raw value, so the user can handle the error in a custom mapper.
                        return text;
                    }
                }
            }
        }

#if NET
        // The SqlClient accepts TimeOnly as parameters, but returns them as TimeSpan.
        // Since we don't support TimeSpan, we can convert it back to TimeOnly.
        if (value is TimeSpan timeSpan)
        {
            return new TimeOnly(timeSpan.Ticks);
        }
#endif

        return value;
    }

    // This is the only method used by the default mapper.
    public object? this[string key]
    {
        get => this.Unwrap(key, sqlDataReader[key]);
        set => throw new InvalidOperationException();
    }

    public ICollection<string> Keys => this.GetDictionary().Keys;

    public ICollection<object?> Values => this.GetDictionary().Values;

    public int Count => sqlDataReader.FieldCount;

    public bool IsReadOnly => true;

    public void Add(string key, object? value) => throw new InvalidOperationException();

    public void Add(KeyValuePair<string, object?> item) => throw new InvalidOperationException();

    public void Clear() => throw new InvalidOperationException();

    public bool Contains(KeyValuePair<string, object?> item)
        => this.TryGetValue(item.Key, out var value) && Equals(value, item.Value);

    public bool ContainsKey(string key)
    {
        try
        {
            return sqlDataReader.GetOrdinal(key) >= 0;
        }
        catch (IndexOutOfRangeException)
        {
            return false;
        }
    }

    public void CopyTo(KeyValuePair<string, object?>[] array, int arrayIndex)
        => ((ICollection<KeyValuePair<string, object?>>)this.GetDictionary()).CopyTo(array, arrayIndex);

    public IEnumerator<KeyValuePair<string, object?>> GetEnumerator()
        => this.GetDictionary().GetEnumerator();

    IEnumerator IEnumerable.GetEnumerator()
        => this.GetDictionary().GetEnumerator();

    public bool Remove(string key) => throw new InvalidOperationException();

    public bool Remove(KeyValuePair<string, object?> item) => throw new InvalidOperationException();

    public bool TryGetValue(string key, out object? value)
    {
        try
        {
            value = this.Unwrap(key, sqlDataReader[key]);
            return true;
        }
        catch (IndexOutOfRangeException)
        {
            value = default;
            return false;
        }
    }

    private Dictionary<string, object?> GetDictionary()
    {
        if (this._dictionary is null)
        {
            Dictionary<string, object?> dictionary = new(sqlDataReader.FieldCount, StringComparer.Ordinal);
            for (int i = 0; i < sqlDataReader.FieldCount; i++)
            {
                string name = sqlDataReader.GetName(i);
                dictionary.Add(name, this.Unwrap(name, sqlDataReader[i]));
            }
            this._dictionary = dictionary;
        }
        return this._dictionary;
    }
}
