// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Moq;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows.Actions;

internal sealed class MockKernelProcessMessageChannel : Mock<IKernelProcessMessageChannel>
{
    public MockKernelProcessMessageChannel()
        : base(MockBehavior.Strict)
    {
        this.Setup(
            channel =>
                channel
                    .EmitEventAsync(It.IsAny<KernelProcessEvent>()))
                    .Returns(ValueTask.CompletedTask);
    }
}
