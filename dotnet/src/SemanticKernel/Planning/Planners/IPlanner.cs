// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Planning.Planners;

public interface IPlanner
{
    Task<Plan> CreatePlanAsync(string goal);
}
