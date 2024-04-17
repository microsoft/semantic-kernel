// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents the result of a Claude function tool call.
/// </summary>
public sealed class AnthropicFunctionToolResult
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicFunctionToolResult"/> class.
    /// </summary>
    /// <param name="toolCall">The called function.</param>
    /// <param name="functionResult">The result of the function.</param>
    /// <param name="toolUseId">The id of tool returned by the claude.</param>
    public AnthropicFunctionToolResult(AnthropicFunctionToolCall toolCall, FunctionResult functionResult, string? toolUseId)
    {
        Verify.NotNull(toolCall);
        Verify.NotNull(functionResult);

        this.FunctionResult = functionResult;
        this.FullyQualifiedName = toolCall.FullyQualifiedName;
        this.ToolUseId = toolUseId;
    }

    /// <summary>
    /// Gets the result of the function.
    /// </summary>
    public FunctionResult FunctionResult { get; }

    /// <summary>Gets the fully-qualified name of the function.</summary>
    /// <seealso cref="AnthropicFunctionToolCall.FullyQualifiedName">ClaudeFunctionToolCall.FullyQualifiedName</seealso>
    public string FullyQualifiedName { get; }

    /// <summary>
    /// The id of tool returned by the claude.
    /// </summary>
    public string? ToolUseId { get; }
}
