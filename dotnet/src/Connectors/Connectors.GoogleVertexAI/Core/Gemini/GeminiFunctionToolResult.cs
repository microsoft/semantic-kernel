// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

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
        this.FunctionResult = functionResult;
        this.FullyQualifiedName = toolCall.FullyQualifiedName;
    }

    /// <summary>
    /// Gets the result of the function.
    /// </summary>
    public FunctionResult FunctionResult { get; }

    /// <summary>Gets the fully-qualified name of the function.</summary>
    /// <remarks>
    /// This is the concatenation of the <see cref="KernelPlugin"/>.<see cref="KernelPlugin.Name"/>
    /// and the <see cref="KernelFunction"/>.<see cref="KernelFunction.Name"/>,
    /// separated by <see cref="GeminiFunction.NameSeparator"/>. If there is no <see cref="KernelPlugin"/>.<see cref="KernelPlugin.Name"/>,
    /// this is the same as <see cref="KernelFunction"/>.<see cref="KernelFunction.Name"/>.
    /// </remarks>
    public string FullyQualifiedName { get; }
}
