// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;
using Moq;

#pragma warning disable CS8620 // Argument cannot be used for parameter due to differences in the nullability of reference types.

internal static class MoqExtensions
{
    public static void VerifyLog<T>(this Mock<ILogger<T>> logger, LogLevel logLevel, string containsMessage, Times times)
    {
        logger.Verify(
            x => x.Log(
                It.Is<LogLevel>(l => l == logLevel),
                It.IsAny<EventId>(),
                It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains(containsMessage)),
                It.IsAny<Exception>(),
                It.IsAny<Func<It.IsAnyType, Exception, string>>()),
            times);
    }

    public static void VerifyLog(this Mock<ILogger> logger, LogLevel logLevel, string containsMessage, Times times)
    {
        logger.Verify(
            x => x.Log(
                It.Is<LogLevel>(l => l == logLevel),
                It.IsAny<EventId>(),
                It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains(containsMessage)),
                It.IsAny<Exception>(),
                It.IsAny<Func<It.IsAnyType, Exception, string>>()),
            times);
    }
}
