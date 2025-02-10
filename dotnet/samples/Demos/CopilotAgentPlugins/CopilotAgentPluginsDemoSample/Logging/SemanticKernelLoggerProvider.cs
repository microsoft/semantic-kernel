// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

public class SemanticKernelLoggerProvider : ILoggerProvider, IDisposable
{
    public ILogger CreateLogger(string categoryName)
    {
        return new SemanticKernelLogger();
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            // Dispose managed resources here.
        }

        // Dispose unmanaged resources here.
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }
}
