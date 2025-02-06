using Microsoft.Extensions.Logging;

public class SemanticKernelLoggerProvider : ILoggerProvider
{
    public ILogger CreateLogger(string categoryName)
    {
        return new SemanticKernelLogger();
    }

    public void Dispose() { }
}
