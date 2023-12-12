// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;

#pragma warning disable CA1710 // Identifiers should have correct suffix

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides a collection of arguments for operations such as <see cref="KernelFunction"/>'s InvokeAsync
/// and <see cref="IPromptTemplate"/>'s RenderAsync.
/// </summary>
/// <remarks>
/// A <see cref="KernelArguments"/> is a dictionary of argument names and values. It also carries a
/// <see cref="PromptExecutionSettings"/>, accessible via the <see cref="ExecutionSettings"/> property.
/// </remarks>
public sealed class KernelArguments : IDictionary<string, object?>, IReadOnlyDictionary<string, object?>
{
    /// <summary>Dictionary of name/values for all the arguments in the instance.</summary>
    private readonly Dictionary<string, object?> _arguments;

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelArguments"/> class with the specified AI execution settings.
    /// </summary>
    /// <param name="executionSettings">The prompt execution settings.</param>
    public KernelArguments(PromptExecutionSettings? executionSettings = null)
    {
        this._arguments = new(StringComparer.OrdinalIgnoreCase);
        this.ExecutionSettings = executionSettings;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelArguments"/> class that contains elements copied from the specified <see cref="IDictionary{TKey, TValue}"/>.
    /// </summary>
    /// <param name="source">The <see cref="IDictionary{TKey, TValue}"/> whose elements are copied the new <see cref="KernelArguments"/>.</param>
    /// <param name="executionSettings">The prompt execution settings.</param>
    /// <remarks>
    /// If <paramref name="executionSettings"/> is non-null, it is used as the <see cref="ExecutionSettings"/> for this new instance.
    /// Otherwise, if the source is a <see cref="KernelArguments"/>, its <see cref="ExecutionSettings"/> are used.
    /// </remarks>
    public KernelArguments(IDictionary<string, object?> source, PromptExecutionSettings? executionSettings = null)
    {
        Verify.NotNull(source);

        this._arguments = new(source, StringComparer.OrdinalIgnoreCase);
        this.ExecutionSettings = executionSettings ?? (source as KernelArguments)?.ExecutionSettings;
    }

    /// <summary>
    /// Gets or sets the prompt execution settings.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings { get; set; }

    /// <summary>
    /// Gets the number of arguments contained in the <see cref="KernelArguments"/>.
    /// </summary>
    public int Count => this._arguments.Count;

    /// <summary>Adds the specified argument name and value to the <see cref="KernelArguments"/>.</summary>
    /// <param name="name">The name of the argument to add.</param>
    /// <param name="value">The value of the argument to add.</param>
    /// <exception cref="ArgumentNullException"><paramref name="name"/> is null.</exception>
    /// <exception cref="ArgumentException">An argument with the same name already exists in the <see cref="KernelArguments"/>.</exception>
    public void Add(string name, object? value)
    {
        Verify.NotNull(name);
        this._arguments.Add(name, value);
    }

    /// <summary>Removes the argument value with the specified name from the <see cref="KernelArguments"/>.</summary>
    /// <param name="name">The name of the argument value to remove.</param>
    /// <exception cref="ArgumentNullException"><paramref name="name"/> is null.</exception>
    public bool Remove(string name)
    {
        Verify.NotNull(name);
        return this._arguments.Remove(name);
    }

    /// <summary>Removes all arguments names and values from the <see cref="KernelArguments"/>.</summary>
    /// <remarks>
    /// This does not affect the <see cref="ExecutionSettings"/> property. To clear it as well, set it to null.
    /// </remarks>
    public void Clear() => this._arguments.Clear();

    /// <summary>Determines whether the <see cref="KernelArguments"/> contains an argument with the specified name.</summary>
    /// <param name="name">The name of the argument to locate.</param>
    /// <returns>true if the arguments contains an argument with the specified named; otherwise, false.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="name"/> is null.</exception>
    public bool ContainsName(string name)
    {
        Verify.NotNull(name);
        return this._arguments.ContainsKey(name);
    }

    /// <summary>Gets the value associated with the specified argument name.</summary>
    /// <param name="name">The name of the argument value to get.</param>
    /// <param name="value">
    /// When this method returns, contains the value associated with the specified name,
    /// if the name is found; otherwise, null.
    /// </param>
    /// <returns>true if the arguments contains an argument with the specified name; otherwise, false.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="name"/> is null.</exception>
    public bool TryGetValue(string name, out object? value)
    {
        Verify.NotNull(name);
        return this._arguments.TryGetValue(name, out value);
    }

    /// <summary>Gets or sets the value associated with the specified argument name.</summary>
    /// <param name="name">The name of the argument value to get or set.</param>
    /// <exception cref="ArgumentNullException"><paramref name="name"/> is null.</exception>
    public object? this[string name]
    {
        get
        {
            Verify.NotNull(name);
            return this._arguments[name];
        }
        set
        {
            Verify.NotNull(name);
            this._arguments[name] = value;
        }
    }

    /// <summary>Gets an <see cref="ICollection{String}"/> of all of the arguments' names.</summary>
    public ICollection<string> Names => this._arguments.Keys;

    /// <summary>Gets an <see cref="ICollection{String}"/> of all of the arguments' values.</summary>
    public ICollection<object?> Values => this._arguments.Values;

    #region Interface implementations
    /// <inheritdoc/>
    ICollection<string> IDictionary<string, object?>.Keys => this._arguments.Keys;

    /// <inheritdoc/>
    IEnumerable<string> IReadOnlyDictionary<string, object?>.Keys => this._arguments.Keys;

    /// <inheritdoc/>
    IEnumerable<object?> IReadOnlyDictionary<string, object?>.Values => this._arguments.Values;

    /// <inheritdoc/>
    bool ICollection<KeyValuePair<string, object?>>.IsReadOnly => false;

    /// <inheritdoc/>
    object? IReadOnlyDictionary<string, object?>.this[string key] => this._arguments[key];

    /// <inheritdoc/>
    object? IDictionary<string, object?>.this[string key]
    {
        get => this._arguments[key];
        set => this._arguments[key] = value;
    }

    /// <inheritdoc/>
    void IDictionary<string, object?>.Add(string key, object? value) => this._arguments.Add(key, value);

    /// <inheritdoc/>
    bool IDictionary<string, object?>.ContainsKey(string key) => this._arguments.ContainsKey(key);

    /// <inheritdoc/>
    bool IDictionary<string, object?>.Remove(string key) => this._arguments.Remove(key);

    /// <inheritdoc/>
    bool IDictionary<string, object?>.TryGetValue(string key, out object? value) => this._arguments.TryGetValue(key, out value);

    /// <inheritdoc/>
    void ICollection<KeyValuePair<string, object?>>.Add(KeyValuePair<string, object?> item) => this._arguments.Add(item.Key, item.Value);

    /// <inheritdoc/>
    bool ICollection<KeyValuePair<string, object?>>.Contains(KeyValuePair<string, object?> item) => ((ICollection<KeyValuePair<string, object?>>)this._arguments).Contains(item);

    /// <inheritdoc/>
    void ICollection<KeyValuePair<string, object?>>.CopyTo(KeyValuePair<string, object?>[] array, int arrayIndex) => ((ICollection<KeyValuePair<string, object?>>)this._arguments).CopyTo(array, arrayIndex);

    /// <inheritdoc/>
    bool ICollection<KeyValuePair<string, object?>>.Remove(KeyValuePair<string, object?> item) => this._arguments.Remove(item.Key);

    /// <inheritdoc/>
    IEnumerator<KeyValuePair<string, object?>> IEnumerable<KeyValuePair<string, object?>>.GetEnumerator() => this._arguments.GetEnumerator();

    /// <inheritdoc/>
    IEnumerator IEnumerable.GetEnumerator() => this._arguments.GetEnumerator();

    /// <inheritdoc/>
    bool IReadOnlyDictionary<string, object?>.ContainsKey(string key) => this._arguments.ContainsKey(key);

    /// <inheritdoc/>
    bool IReadOnlyDictionary<string, object?>.TryGetValue(string key, out object? value) => this._arguments.TryGetValue(key, out value);
    #endregion
}
