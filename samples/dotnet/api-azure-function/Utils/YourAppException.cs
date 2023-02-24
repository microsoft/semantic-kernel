// Copyright (c) Microsoft. All rights reserved.

using System;

namespace SemanticKernelFunction.Utils;

public class YourAppException : Exception
{
    public YourAppException(string message) : base(message)
    {
    }
}
