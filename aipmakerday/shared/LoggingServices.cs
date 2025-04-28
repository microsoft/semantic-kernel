namespace SemanticKernel.HelloAgents.Internal;

using Microsoft.Extensions.Logging;

internal static class LoggingServices
{
    public static ILoggerFactory CreateLoggerFactory() =>
        LoggerFactory.Create(
            builder =>
            {
                builder.AddDebug();
            });
}
