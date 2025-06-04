// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.Agents.Runtime.Internal;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Represents a topic identifier that defines the scope of a broadcast message.
/// The agent runtime implements a publish-subscribe model through its broadcast API,
/// where messages must be published with a specific topic.
///
/// See the Python equivalent:
/// <see href="https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md#type">CloudEvents Type Specification</see>.
/// </summary>
public struct TopicId : IEquatable<TopicId>
{
    /// <summary>
    /// The default source value used when no source is explicitly provided.
    /// </summary>
    public const string DefaultSource = "default";

    /// <summary>
    /// The separator character for the string representation of the topic.
    /// </summary>
    public const string Separator = "/";

    /// <summary>
    /// Gets the type of the event that this <see cref="TopicId"/> represents.
    /// This adheres to the CloudEvents specification.
    ///
    /// Must match the pattern: <c>^[\w\-\.\:\=]+$</c>.
    ///
    /// Learn more here:
    /// <see href="https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md#type">CloudEvents Type</see>.
    /// </summary>
    public string Type { get; }

    /// <summary>
    /// Gets the source that identifies the context in which an event happened.
    /// This adheres to the CloudEvents specification.
    ///
    /// Learn more here:
    /// <see href="https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md#source-1">CloudEvents Source</see>.
    /// </summary>
    public string Source { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TopicId"/> struct.
    /// </summary>
    /// <param name="type">The type of the topic.</param>
    /// <param name="source">The source of the event. Defaults to <see cref="DefaultSource"/> if not specified.</param>
    public TopicId(string type, string source = DefaultSource)
    {
        this.Type = type;
        this.Source = source;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="TopicId"/> struct from a tuple.
    /// </summary>
    /// <param name="kvPair">A tuple containing the topic type and source.</param>
    public TopicId((string Type, string Source) kvPair) : this(kvPair.Type, kvPair.Source)
    {
    }

    /// <summary>
    /// Converts a string in the format "type/source" into a <see cref="TopicId"/>.
    /// </summary>
    /// <param name="maybeTopicId">The topic ID string.</param>
    /// <returns>An instance of <see cref="TopicId"/>.</returns>
    /// <exception cref="FormatException">Thrown when the string is not in the valid "type/source" format.</exception>
    public static TopicId FromStr(string maybeTopicId) => new(maybeTopicId.ToKeyValuePair(nameof(Type), nameof(Source)));

    /// <summary>
    /// Returns the string representation of the <see cref="TopicId"/>.
    /// </summary>
    /// <returns>A string in the format "type/source".</returns>
    public override readonly string ToString() => $"{this.Type}{Separator}{this.Source}";

    /// <summary>
    /// Determines whether the specified object is equal to the current <see cref="TopicId"/>.
    /// </summary>
    /// <param name="obj">The object to compare with the current instance.</param>
    /// <returns><c>true</c> if the specified object is equal to the current <see cref="TopicId"/>; otherwise, <c>false</c>.</returns>
    public override readonly bool Equals([NotNullWhen(true)] object? obj)
    {
        if (obj is TopicId other)
        {
            return this.Type == other.Type && this.Source == other.Source;
        }

        return false;
    }

    /// <summary>
    /// Determines whether the specified object is equal to the current <see cref="TopicId"/>.
    /// </summary>
    /// <param name="other">The object to compare with the current instance.</param>
    /// <returns><c>true</c> if the specified object is equal to the current <see cref="TopicId"/>; otherwise, <c>false</c>.</returns>
    public readonly bool Equals([NotNullWhen(true)] TopicId other)
    {
        return this.Type == other.Type && this.Source == other.Source;
    }

    /// <summary>
    /// Returns a hash code for this <see cref="TopicId"/>.
    /// </summary>
    /// <returns>A hash code for the current instance.</returns>
    public override readonly int GetHashCode()
    {
        return HashCode.Combine(this.Type, this.Source);
    }

    /// <summary>
    /// Explicitly converts a string to a <see cref="TopicId"/>.
    /// </summary>
    /// <param name="id">The string representation of a topic ID.</param>
    /// <returns>An instance of <see cref="TopicId"/>.</returns>
    public static explicit operator TopicId(string id) => FromStr(id);

    // TODO: Implement < for wildcard matching (type, *)
    // == => <
    // Type == other.Type => <
    /// <summary>
    /// Determines whether the given <see cref="TopicId"/> matches another topic.
    /// </summary>
    /// <param name="other">The topic ID to compare against.</param>
    /// <returns>
    /// <c>true</c> if the topic types are equal; otherwise, <c>false</c>.
    /// </returns>
    public readonly bool IsWildcardMatch(TopicId other)
    {
        return this.Type == other.Type;
    }

    /// <inheritdoc/>
    public static bool operator ==(TopicId left, TopicId right)
    {
        return left.Equals(right);
    }

    /// <inheritdoc/>
    public static bool operator !=(TopicId left, TopicId right)
    {
        return !(left == right);
    }
}
