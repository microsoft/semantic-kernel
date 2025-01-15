// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a base class for function name policies that handle function names.
/// The policy classes create function fully qualified names (FQN) that are provided to the AI model
/// and parse them back into the plugin name and function name when the functions are called
/// by the AI model.
/// </summary>
[Experimental("SKEXP0001")]
public abstract class FunctionNamePolicy
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionNamePolicy"/> class.
    /// </summary>
    internal FunctionNamePolicy()
    {
    }

    /// <summary>
    /// Gets the default function name policy that uses the hyphen separator ("-") for creating and parsing function FQNs.
    /// </summary>
    public static FunctionNamePolicy Default { get; } = new DefaultFunctionNamePolicy("-");

    /// <summary>
    /// Gets the function name policy that uses only the function name to create function FQNs.
    /// </summary>
    /// <remarks>
    /// This policy does not use plugin name to create function FQNs.
    /// For example, if your plugin name is "foo" and your function name is "bar" the function's FQN will be "bar" instead of "foo-bar."
    /// </remarks>
    public static FunctionNamePolicy FunctionNameOnly { get; } = new FunctionNameOnlyPolicy();

    /// <summary>
    /// Gets a custom function name policy that allows specifying a custom separator for creating and parsing function FQNs.
    /// Additionally, it allows specifying a custom delegate for parsing the function FQN.
    /// </summary>
    /// <param name="separator">A separator to use for creating and parsing function FQNs.</param>
    /// <param name="parseFunctionFqnDelegate">Delegate to parse the function FQN.</param>
    /// <returns>A custom function name policy.</returns>
    public static FunctionNamePolicy Custom(string separator, ParseFunctionFqn? parseFunctionFqnDelegate = null)
    {
        return new DefaultFunctionNamePolicy(separator, parseFunctionFqnDelegate);
    }

    /// <summary>
    /// Retrieves the FQN of a function.
    /// </summary>
    /// <param name="context">The context that contains the name of the function and its plugin.</param>
    /// <returns>The function FQN.</returns>
    public abstract string GetFunctionFqn(GetFunctionFqnContext context);

    /// <summary>
    /// Parses the FQN of a function into the plugin name and the function name.
    /// </summary>
    /// <param name="context">The context that contains the FQN of the function.</param>
    /// <returns>The plugin name and the function name.</returns>
    public abstract (string? PluginName, string FunctionName) ParseFunctionFqn(ParseFunctionFqnContext context);

    internal class DefaultFunctionNamePolicy(string functionNameSeparator, ParseFunctionFqn? parseFunctionFqnDelegate = null) : FunctionNamePolicy
    {
        public override string GetFunctionFqn(GetFunctionFqnContext context)
        {
            return FunctionName.ToFullyQualifiedName(context.FunctionName, context.PluginName, functionNameSeparator);
        }

        public override (string? PluginName, string FunctionName) ParseFunctionFqn(ParseFunctionFqnContext context)
        {
            // Use custom parsing delegate if provided
            if (parseFunctionFqnDelegate is not null)
            {
                return parseFunctionFqnDelegate.Invoke(context);
            }

            var fn = FunctionName.Parse(context.FunctionFqn, functionNameSeparator);

            return (fn.PluginName, fn.Name);
        }
    }

    internal class FunctionNameOnlyPolicy : FunctionNamePolicy
    {
        public override string GetFunctionFqn(GetFunctionFqnContext context)
        {
            return context.FunctionName;
        }

        public override (string? PluginName, string FunctionName) ParseFunctionFqn(ParseFunctionFqnContext context)
        {
            return (null, context.FunctionFqn);
        }
    }
}
