// Copyright (c) Microsoft. All rights reserved.

using System;

namespace SemanticKernel.IntegrationTests.TestExtensions;

public class SkipTestException : Exception
{
    public SkipTestException(string reason)
        : base(reason)
    {
    }
}
