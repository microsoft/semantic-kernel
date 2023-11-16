// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel.AI;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Native function streaming result update.
/// </summary>
public sealed class StreamingNativeResultUpdate : StreamingResultChunk
{
    /// <inheritdoc/>
    public override string Type => "native_result_update";

    /// <inheritdoc/>
    public override int ResultIndex => 0;

    /// <summary>
    /// Native object value that represents the update
    /// </summary>
    public object Value { get; }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        if (this.Value is byte[])
        {
            return (byte[])this.Value;
        }

        return Encoding.UTF8.GetBytes(this.Value?.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Value.ToString();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingNativeResultUpdate"/> class.
    /// </summary>
    /// <param name="update">Underlying object that represents the update</param>
    public StreamingNativeResultUpdate(object update)
    {
        this.Value = update;
    }
}
