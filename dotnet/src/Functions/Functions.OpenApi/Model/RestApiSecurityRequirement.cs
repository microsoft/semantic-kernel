// Copyright (c) Microsoft. All rights reserved.

using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API security requirement object.
/// </summary>
#pragma warning disable CA1710 // Identifiers should have correct suffix
public sealed class RestApiSecurityRequirement : IDictionary<RestApiSecurityScheme, IList<string>>, IReadOnlyDictionary<RestApiSecurityScheme, IList<string>>
#pragma warning restore CA1710 // Identifiers should have correct suffix
{
    /// <summary>Creates an instance of a <see cref="RestApiSecurityRequirement"/> class.</summary>
    /// <param name="dictionary">Dictionary containing the security schemes.</param>
    internal RestApiSecurityRequirement(IDictionary<RestApiSecurityScheme, IList<string>>? dictionary = null)
    {
        this._dictionary = dictionary ?? new Dictionary<RestApiSecurityScheme, IList<string>>();
    }

    /// <summary>Gets the number of elements contained in the <see cref="RestApiSecurityRequirement"/>.</summary>
    public int Count => this._dictionary.Count;

    /// <summary>Adds the specified security scheme to the <see cref="RestApiSecurityRequirement"/>.</summary>
    /// <param name="key">The security scheme to add.</param>
    /// <param name="value">The security scheme scopes.</param>
    public void Add(RestApiSecurityScheme key, IList<string> value)
    {
        this._freezable.ThrowIfFrozen();
        this._dictionary.Add(key, value);
    }

    /// <summary>Removes the security scheme with the specified key from the <see cref="RestApiSecurityRequirement"/>.</summary>
    /// <param name="key">The security scheme to remove.</param>
    public bool Remove(RestApiSecurityScheme key)
    {
        this._freezable.ThrowIfFrozen();
        return this._dictionary.Remove(key);
    }

    /// <summary>Removes all the security schemes from the <see cref="RestApiSecurityRequirement"/>.</summary>
    public void Clear()
    {
        this._freezable.ThrowIfFrozen();
        this._dictionary.Clear();
    }

    /// <summary>Determines whether the <see cref="RestApiSecurityRequirement"/> contains a specific security scheme.</summary>
    /// <param name="key">The security scheme to locate in the <see cref="RestApiSecurityRequirement"/>.</param>
    /// <returns>true if the <see cref="RestApiSecurityRequirement"/> contains an element with the specified key; otherwise, false.</returns>
    public bool ContainsKey(RestApiSecurityScheme key)
    {
        return this._dictionary.ContainsKey(key);
    }

    /// <summary>Get the security scheme scopes associated with the specified security scheme.</summary>
    /// <param name="key">The security scheme to get the scopes for.</param>
    /// <param name="value">When this method returns, contains the security scheme scopes associated
    /// with the specified security scheme, if the security scheme is found; otherwise, the default value
    /// for the type of the value parameter. This parameter is passed uninitialized.
    /// </param>
    /// <returns>true if the <see cref="RestApiSecurityRequirement"/> contains an element with the specified key; otherwise, false.</returns>
    public bool TryGetValue(RestApiSecurityScheme key, [MaybeNullWhen(false)] out IList<string> value)
    {
        return this._dictionary.TryGetValue(key, out value);
    }

    /// <summary>Gets or sets the security scheme scopes associated with the specified security scheme.</summary>
    /// <param name="key">The security scheme to get or set the scopes for.</param>
#pragma warning disable CA1043 // Use Integral Or String Argument For Indexers
    public IList<string> this[RestApiSecurityScheme key]
#pragma warning restore CA1043 // Use Integral Or String Argument For Indexers
    {
        get => this._dictionary[key];
        set
        {
            this._freezable.ThrowIfFrozen();
            this._dictionary[key] = value;
        }
    }

    /// <summary>Gets an <see cref="ICollection{RestApiSecurityScheme}"/> of all of the security schemes.</summary>
    public ICollection<RestApiSecurityScheme> Keys => this._dictionary.Keys;

    /// <summary>Gets an <see cref="ICollection{IList}"/> of all of the security scheme scopes.</summary>
    public ICollection<IList<string>> Values => this._dictionary.Values;

    internal void Freeze()
    {
        foreach (var item in this)
        {
            // Freeze the security scheme
            item.Key.Freeze();

            // Freeze the security scheme scopes
            this[item.Key] = new ReadOnlyCollection<string>(item.Value);
        }

        // Freeze the object
        this._freezable.Freeze();
    }

    #region Interface implementations
    /// <inheritdoc/>
    ICollection<RestApiSecurityScheme> IDictionary<RestApiSecurityScheme, IList<string>>.Keys => this._dictionary.Keys;

    /// <inheritdoc/>
    IEnumerable<RestApiSecurityScheme> IReadOnlyDictionary<RestApiSecurityScheme, IList<string>>.Keys => this._dictionary.Keys;

    /// <inheritdoc/>
    IEnumerable<IList<string>> IReadOnlyDictionary<RestApiSecurityScheme, IList<string>>.Values => this._dictionary.Values;

    /// <inheritdoc/>
    bool ICollection<KeyValuePair<RestApiSecurityScheme, IList<string>>>.IsReadOnly => this._freezable.IsFrozen;

    /// <inheritdoc/>
    IList<string> IReadOnlyDictionary<RestApiSecurityScheme, IList<string>>.this[RestApiSecurityScheme key] => this._dictionary[key];

    /// <inheritdoc/>
    IList<string> IDictionary<RestApiSecurityScheme, IList<string>>.this[RestApiSecurityScheme key]
    {
        get => this._dictionary[key];
        set
        {
            this._freezable.ThrowIfFrozen();
            this._dictionary[key] = value;
        }
    }

    /// <inheritdoc/>
    void IDictionary<RestApiSecurityScheme, IList<string>>.Add(RestApiSecurityScheme key, IList<string> value)
    {
        this._freezable.ThrowIfFrozen();
        this._dictionary.Add(key, value);
    }

    /// <inheritdoc/>
    bool IDictionary<RestApiSecurityScheme, IList<string>>.ContainsKey(RestApiSecurityScheme key)
    {
        return this._dictionary.ContainsKey(key);
    }

    /// <inheritdoc/>
    bool IDictionary<RestApiSecurityScheme, IList<string>>.Remove(RestApiSecurityScheme key)
    {
        this._freezable.ThrowIfFrozen();
        return this._dictionary.Remove(key);
    }

    /// <inheritdoc/>
#pragma warning disable CS8769 // Nullability of reference types in value of type does not match target type.
    bool IDictionary<RestApiSecurityScheme, IList<string>>.TryGetValue(RestApiSecurityScheme key, [MaybeNullWhen(false)] out IList<string> value)
    {
        return this._dictionary.TryGetValue(key, out value);
    }
#pragma warning restore CS8769 // Nullability of reference types in value of type does not match target type.

    /// <inheritdoc/>
    void ICollection<KeyValuePair<RestApiSecurityScheme, IList<string>>>.Add(KeyValuePair<RestApiSecurityScheme, IList<string>> item)
    {
        this._freezable.ThrowIfFrozen();
        this._dictionary.Add(item.Key, item.Value);
    }

    /// <inheritdoc/>
    bool ICollection<KeyValuePair<RestApiSecurityScheme, IList<string>>>.Contains(KeyValuePair<RestApiSecurityScheme, IList<string>> item)
    {
        return ((ICollection<KeyValuePair<RestApiSecurityScheme, IList<string>>>)this._dictionary).Contains(item);
    }

    /// <inheritdoc/>
    void ICollection<KeyValuePair<RestApiSecurityScheme, IList<string>>>.CopyTo(KeyValuePair<RestApiSecurityScheme, IList<string>>[] array, int arrayIndex)
    {
        ((ICollection<KeyValuePair<RestApiSecurityScheme, IList<string>>>)this._dictionary).CopyTo(array, arrayIndex);
    }

    /// <inheritdoc/>
    bool ICollection<KeyValuePair<RestApiSecurityScheme, IList<string>>>.Remove(KeyValuePair<RestApiSecurityScheme, IList<string>> item)
    {
        this._freezable.ThrowIfFrozen();
        return this._dictionary.Remove(item.Key);
    }

    /// <inheritdoc/>
    IEnumerator<KeyValuePair<RestApiSecurityScheme, IList<string>>> IEnumerable<KeyValuePair<RestApiSecurityScheme, IList<string>>>.GetEnumerator()
    {
        return this._dictionary.GetEnumerator();
    }

    /// <inheritdoc/>
    IEnumerator IEnumerable.GetEnumerator()
    {
        return this._dictionary.GetEnumerator();
    }

    /// <inheritdoc/>
    bool IReadOnlyDictionary<RestApiSecurityScheme, IList<string>>.ContainsKey(RestApiSecurityScheme key)
    {
        return this._dictionary.ContainsKey(key);
    }

    /// <inheritdoc/>
#pragma warning disable CS8769 // Nullability of reference types in value of type does not match target type.
    bool IReadOnlyDictionary<RestApiSecurityScheme, IList<string>>.TryGetValue(RestApiSecurityScheme key, [MaybeNullWhen(false)] out IList<string> value)
    {
        return this._dictionary.TryGetValue(key, out value);
    }
#pragma warning restore CS8769 // Nullability of reference types in value of type does not match target type.

    private readonly IDictionary<RestApiSecurityScheme, IList<string>> _dictionary;
    private readonly Freezable _freezable = new();

    #endregion
}
