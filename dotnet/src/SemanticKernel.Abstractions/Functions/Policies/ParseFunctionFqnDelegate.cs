// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Delegate for parsing the FQN of a function.
/// </summary>
/// <param name="context">The context.</param>
/// <returns>The plugin name and the function name.</returns>
[Experimental("SKEXP0001")]
public delegate (string? PluginName, string FunctionName) ParseFunctionFqn(ParseFunctionFqnContext context);
