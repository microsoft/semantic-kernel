// Copyright (c) Microsoft. All rights reserved.

using System;

namespace RepoUtils;

public class YourAppException : Exception
{
    public YourAppException(string message) : base(message)
    {
    }
}
