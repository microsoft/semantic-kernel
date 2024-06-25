// Copyright (c) Microsoft. All rights reserved.

using System;

namespace AIPlugins.AzureFunctions;
internal class BadRequestException : Exception
{
    public BadRequestException(string message) : base(message)
    {
    }

    public BadRequestException(string message, Exception innerException) : base(message, innerException)
    {
    }
}
