// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.AI;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Method function streaming result chunk.
/// </summary>
public sealed class StreamingMethodResultChunk : StreamingResultChunk
{
    /// <inheritdoc/>
    public override string Type => "method_result_chunk";

    /// <inheritdoc/>
    public override int ChoiceIndex => 0;

    /// <summary>
    /// Method object value that represents the chunk
    /// </summary>
    public object Value { get; }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        if (this.Value is byte[])
        {
            return (byte[])this.Value;
        }

        // By default if a native value is not Byte[] we output the UTF8 string representation of the value
        return Encoding.UTF8.GetBytes(this.Value?.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Value.ToString();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingMethodResultChunk"/> class.
    /// </summary>
    /// <param name="innerResultChunk">Underlying object that represents the chunk</param>
    public StreamingMethodResultChunk(object innerResultChunk) : base(innerResultChunk)
    {
        this.Value = innerResultChunk;
    }
}
