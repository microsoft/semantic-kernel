// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function call result content.
/// </summary>
public sealed class FunctionResultContent : KernelContent
{
    /// <summary>
    /// The function call ID.
    /// </summary>
    public string? Id { get; private set; }

    /// <summary>
    /// Gets the fully-qualified name of the function.
    /// </summary>
    public string? FullyQualifiedName { get; private set; }

    /// <summary>
    /// The result of the function call.
    /// </summary>
    public object? Result { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="id">The function call ID.</param>
    /// <param name="fullyQualifiedName">The fully-qualified name of the function.</param>
    /// <param name="result">The function result.</param>
    [JsonConstructor]
    public FunctionResultContent(string? id, string? fullyQualifiedName, object? result)
    {
        this.Id = id;
        this.FullyQualifiedName = fullyQualifiedName;
        this.Result = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="id">The function call ID.</param>
    /// <param name="fullyQualifiedName">The fully-qualified name of the function.</param>
    /// <param name="result">The function result.</param>
    public FunctionResultContent(string? id, string? fullyQualifiedName, FunctionResult result) :
        this(id, fullyQualifiedName, result?.Value)
    {
        this.InnerContent = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="id">The function call ID.</param>
    /// <param name="fullyQualifiedName">The fully-qualified name of the function.</param>
    /// <param name="exception">The function result.</param>
    public FunctionResultContent(string? id, string? fullyQualifiedName, Exception exception) :
        this(id, fullyQualifiedName, exception as object)
    {
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionCallContent">The function call content.</param>
    /// <param name="result">The function result.</param>
    public FunctionResultContent(FunctionCallContent functionCallContent, object? result)
    {
        Verify.NotNull(functionCallContent, nameof(functionCallContent));

        this.Id = functionCallContent.Id;
        this.FullyQualifiedName = functionCallContent.FullyQualifiedName;
        this.Result = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionCallContent">The function call content.</param>
    /// <param name="result">The function result.</param>
    public FunctionResultContent(FunctionCallContent functionCallContent, FunctionResult result) :
        this(functionCallContent, result?.Value)
    {
        this.InnerContent = result;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionCallContent">The function call content.</param>
    /// <param name="exception">The function result.</param>
    public FunctionResultContent(FunctionCallContent functionCallContent, Exception exception) :
        this(functionCallContent, exception as object)
    {
    }
}
