// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Represents a line of a Server-Sent Events (SSE) stream.
/// </summary>
/// <remarks>
/// <a href="https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream">SSE specification</a>
/// </remarks>
[ExcludeFromCodeCoverage]
internal readonly struct SseLine : IEquatable<SseLine>
{
    private readonly string _original;
    private readonly int _colonIndex;
    private readonly int _valueIndex;

    /// <summary>
    /// Represents an empty SSE line.
    /// </summary>
    /// <remarks>
    /// The <see cref="Empty"/> property is a static instance of the <see cref="SseLine"/> struct.
    /// </remarks>
    internal static SseLine Empty { get; } = new(string.Empty, 0, false, null);

    internal SseLine(string original, int colonIndex, bool hasSpaceAfterColon, string? lastEventName)
    {
        this._original = original;
        this._colonIndex = colonIndex;
        this._valueIndex = colonIndex >= 0 ? colonIndex + (hasSpaceAfterColon ? 2 : 1) : -1;
        if (this._valueIndex >= this._original.Length)
        {
            this._valueIndex = -1;
        }

        this.EventName = lastEventName;
    }

    /// <summary>
    /// The name of the last event for the Server-Sent Events (SSE) line.
    /// </summary>
    public string? EventName { get; }

    /// <summary>
    /// Determines whether the SseLine is empty.
    /// </summary>
    public bool IsEmpty => this._original.Length == 0;

    /// <summary>
    /// Gets a value indicating whether the value of the SseLine is empty.
    /// </summary>
    public bool IsValueEmpty => this._valueIndex < 0;

    /// <summary>
    /// Determines whether the SseLine is comment line.
    /// </summary>
    public bool IsComment => !this.IsEmpty && this._original[0] == ':';

    /// <summary>
    /// Represents a field name in a Server-Sent Events (SSE) line.
    /// </summary>
    public ReadOnlyMemory<char> FieldName => this._colonIndex >= 0 ? this._original.AsMemory(0, this._colonIndex) : this._original.AsMemory();

    /// <summary>
    /// Represents a field value in Server-Sent Events (SSE) format.
    /// </summary>
    public ReadOnlyMemory<char> FieldValue => this._valueIndex >= 0 ? this._original.AsMemory(this._valueIndex) : string.Empty.AsMemory();

    /// <inheritdoc />
    public override string ToString() => this._original;

    /// <inheritdoc />
    public bool Equals(SseLine other) => this._original.Equals(other._original, StringComparison.Ordinal);

    /// <inheritdoc />
    public override bool Equals(object? obj) => obj is SseLine other && this.Equals(other);

    /// <inheritdoc />
    public override int GetHashCode() => StringComparer.Ordinal.GetHashCode(this._original);

    /// <summary>
    /// Defines the equality operator for comparing two instances of the SseLine class.
    /// </summary>
    public static bool operator ==(SseLine left, SseLine right) => left.Equals(right);

    /// <summary>
    /// Represents the inequality operator for comparing two SseLine objects.
    /// </summary>
    public static bool operator !=(SseLine left, SseLine right) => !left.Equals(right);
}
