// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Xunit.Abstractions;
using Xunit.Sdk;

namespace SemanticKernel.IntegrationTests.TestExtensions;

internal sealed class SkippableFactMessageBus : IMessageBus
{
    private readonly IMessageBus _innerBus;

    public SkippableFactMessageBus(IMessageBus innerBus)
    {
        this._innerBus = innerBus;
    }

    public int DynamicallySkippedTestCount { get; private set; }

    public void Dispose() { }

    public bool QueueMessage(IMessageSinkMessage message)
    {
        var testFailed = message as ITestFailed;
        if (testFailed != null)
        {
            var exceptionType = testFailed.ExceptionTypes.FirstOrDefault();
            if (exceptionType == typeof(SkipTestException).FullName)
            {
                this.DynamicallySkippedTestCount++;
                return this._innerBus.QueueMessage(new TestSkipped(testFailed.Test, testFailed.Messages.FirstOrDefault()));
            }
        }

        // Nothing we care about, send it on its way
        return this._innerBus.QueueMessage(message);
    }
}
