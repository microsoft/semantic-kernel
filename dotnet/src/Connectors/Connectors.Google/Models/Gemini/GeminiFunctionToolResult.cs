// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents the result of a Gemini function tool call.
/// </summary>
public sealed class GeminiFunctionToolResult
{
    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiFunctionToolResult"/> class.
    /// </summary>
    /// <param name="toolCall">The called function.</param>
    /// <param name="functionResult">The result of the function.</param>
    public GeminiFunctionToolResult(GeminiFunctionToolCall toolCall, FunctionResult functionResult)
    {
        Verify.NotNull(toolCall);
        Verify.NotNull(functionResult);

        this.FunctionResult = functionResult;
        this.FullyQualifiedName = toolCall.FullyQualifiedName;
    }

    /// <summary>
    /// Gets the result of the function.
    /// </summary>
    public FunctionResult FunctionResult { get; }

    /// <summary>Gets the fully-qualified name of the function.</summary>
    /// <seealso cref="GeminiFunctionToolCall.FullyQualifiedName">GeminiFunctionToolCall.FullyQualifiedName</seealso>
    public string FullyQualifiedName { get; }
}
