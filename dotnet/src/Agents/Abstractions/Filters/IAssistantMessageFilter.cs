// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// %%%
/// </summary>
public interface IAssistantMessageFilter
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="context">The <see cref="AssistantMessageContext"/> containing the result of the function's invocation.</param>
    Task<IEnumerable<KernelContent>> OnFilterAssistantMessage(AssistantMessageContext context);
}
