// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Delegate to the next filter in pipeline or functon itself.
/// </summary>
/// <param name="context">Instance of <see cref="FunctionInvocationContext"/> with function invocation details.</param>
[Experimental("SKEXP0001")]
public delegate Task FunctionInvocationCallback(FunctionInvocationContext context);
