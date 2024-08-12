// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;

public interface ITestCondition
{
    ValueTask<bool> IsMetAsync();

    string SkipReason { get; }
}
