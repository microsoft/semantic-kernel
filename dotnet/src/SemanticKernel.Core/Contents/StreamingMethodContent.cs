// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a manufactured streaming content from a single function result.
/// </summary>
public sealed class StreamingMethodContent : StreamingKernelContent
{
    /// <summary>
    /// Gets the result of the function invocation.
    /// </summary>
    public object Content { get; }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        if (this.Content is byte[] bytes)
        {
            return bytes;
        }

        // By default if a native value is not Byte[] we output the UTF8 string representation of the value
        return this.Content?.ToString() is string s ?
            Encoding.UTF8.GetBytes(s) :
            Array.Empty<byte>();
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Content.ToString() ?? string.Empty;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingMethodContent"/> class.
    /// </summary>
    /// <param name="innerContent">Underlying object that represents the chunk content.</param>
    /// <param name="metadata">Additional metadata associated with the content.</param>
    public StreamingMethodContent(object innerContent, IReadOnlyDictionary<string, object?>? metadata = null) : base(innerContent, metadata: metadata)
    {
        this.Content = innerContent;
    }
}
