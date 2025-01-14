// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function streaming call requested by LLM.
/// </summary>
public class StreamingFunctionCallUpdateContent : StreamingKernelContent
{
    /// <summary>
    /// The function call ID.
    /// </summary>
    public string? CallId { get; init; }

    /// <summary>
    /// The function name.
    /// </summary>
    public string? Name { get; init; }

    /// <summary>
    /// The function arguments that can come as full or partial.
    /// </summary>
    public string? Arguments { get; init; }

    /// <summary>
    /// The function call index.
    /// </summary>
    public int FunctionCallIndex { get; init; }

    /// <summary>
    /// Index of the request that produced this message content.
    /// </summary>
    [Experimental("SKEXP0001")]
    public int RequestIndex { get; init; } = 0;

    /// <summary>
    /// Creates a new instance of the <see cref="StreamingFunctionCallUpdateContent"/> class.
    /// </summary>
    /// <param name="callId">The function call ID.</param>
    /// <param name="name">The function name.</param>
    /// <param name="arguments">The function original arguments.</param>
    /// <param name="functionCallIndex">The function call index.</param>
    public StreamingFunctionCallUpdateContent(string? callId = null, string? name = null, string? arguments = null, int functionCallIndex = 0)
    {
        this.CallId = callId;
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
        return Encoding.UTF8.GetBytes(this.ToString());
    }
}
