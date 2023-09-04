// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Planning.Structured;

using System.Threading;
using System.Threading.Tasks;


public interface IStructuredPlanner
{
    Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default);
}
