// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

public static class KernelPlanningExtensions
{
    public static Task<IPlan> RunAsync(this IKernel kernel, IPlan plan)
    {
        return kernel.RunAsync(plan.State, plan, CancellationToken.None);
    }

    public static Task<IPlan> RunAsync(this IKernel kernel, IPlan plan, CancellationToken cancellationToken)
    {
        return kernel.RunAsync(plan.State, plan, cancellationToken);
    }

    public static Task<IPlan> RunAsync(this IKernel kernel, string input, IPlan plan)
    {
        return kernel.RunAsync(input, plan, CancellationToken.None);
    }

    public static Task<IPlan> RunAsync(this IKernel kernel, string input, IPlan plan, CancellationToken cancellationToken)
    {
        return kernel.RunAsync(new ContextVariables(input), plan, cancellationToken);
    }

    public static Task<IPlan> RunAsync(this IKernel kernel, ContextVariables variables, IPlan plan)
    {
        return kernel.RunAsync(variables, plan, CancellationToken.None);
    }

    public static Task<IPlan> RunAsync(this IKernel kernel, ContextVariables variables, IPlan plan, CancellationToken cancellationToken)
    {
        return plan.RunNextStepAsync(kernel, variables, cancellationToken);
    }
}
