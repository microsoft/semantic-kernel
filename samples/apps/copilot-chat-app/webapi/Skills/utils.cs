using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.Service.Skills;

/// <summary>
/// Utility methods for skills.
/// </summary>
internal static class Utils
{
    /// <summary>
    /// Creates a new context with a clone of the variables from the given context.
    /// This is useful when you want to modify the variables in a context without
    /// affecting the original context.
    /// </summary>
    /// <param name="context">The context to copy.</param>
    /// <returns>A new context with a clone of the variables.</returns>
    internal static SKContext CopyContextWithVariablesClone(SKContext context)
    {
        return new SKContext(
            context.Variables.Clone(),
            context.Memory,
            context.Skills,
            context.Log,
            context.CancellationToken
        );
    }
}
