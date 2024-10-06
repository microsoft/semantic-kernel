<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;

/// <summary>
/// Flow executor interface
/// </summary>
public interface IFlowExecutor
{
    /// <summary>
    /// Execute the <see cref="Flow"/>
    /// </summary>
    /// <param name="flow">Flow</param>
    /// <param name="sessionId">Session id, which is used to track the execution status.</param>
    /// <param name="input">The input from client to continue the execution.</param>
    /// <param name="kernelArguments">The request kernel arguments </param>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
    /// <returns>The execution context</returns>
    Task<FunctionResult> ExecuteFlowAsync(Flow flow, string sessionId, string input, KernelArguments kernelArguments);
    /// <param name="contextVariables">The request context variables </param>
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    /// <returns>The execution context</returns>
    Task<FunctionResult> ExecuteFlowAsync(Flow flow, string sessionId, string input, KernelArguments kernelArguments);
}
