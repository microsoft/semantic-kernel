// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function streaming call requested by LLM.
/// </summary>
[Experimental("SKEXP0001")]
public class StreamingFunctionCallUpdateContent : StreamingKernelContent
{
    /// <summary>
    /// The function call ID that can come as full or partial.
    /// </summary>
    public string? Id { get; }

    /// <summary>
    /// The function name that can come as full or partial.
    /// </summary>
    public string? Name { get; }

    /// <summary>
    /// The function arguments that can come as full or partial.
    /// </summary>
    public string? Arguments { get; }

    /// <summary>
    /// The function call index.
    /// </summary>
    public int FunctionCallIndex { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="StreamingFunctionCallUpdateContent"/> class.
    /// </summary>
    /// <param name="id">The function call ID.</param>
    /// <param name="name">The function name.</param>
    /// <param name="arguments">The function original arguments.</param>
    /// <param name="functionCallIndex">The function call index.</param>
    public StreamingFunctionCallUpdateContent(string? id = null, string? name = null, string? arguments = null, int functionCallIndex = 0)
    {
        this.Id = id;
        this.Name = name;
        this.Arguments = arguments;
        this.FunctionCallIndex = functionCallIndex;
    }

    /// <inheritdoc />
    public override string ToString()
    {
        return nameof(StreamingFunctionCallUpdateContent);
    }

    /// <inheritdoc />
    public override byte[] ToByteArray()
    {
        return [];
    }
}
