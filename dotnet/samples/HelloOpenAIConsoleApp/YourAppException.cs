// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
#pragma warning disable CS1591

namespace RepoUtils;

public class YourAppException : Exception
{
    public YourAppException() : base()
    {
    }

    public YourAppException(string message) : base(message)
    {
    }

    public YourAppException(string message, Exception innerException) : base(message, innerException)
    {
    }
}
