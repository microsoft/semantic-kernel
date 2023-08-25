// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Interface for standard Semantic Kernel callable plan.
/// </summary>
public interface IPlan : ISKFunction,
    ISKFunctionEventSupport<FunctionInvokingEventArgs>,
    ISKFunctionEventSupport<FunctionInvokedEventArgs>
{
}
