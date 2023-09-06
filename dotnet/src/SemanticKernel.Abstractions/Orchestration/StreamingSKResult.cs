// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Orchestration;

public abstract record StreamingSKResult
{
    public SKContext InputSKContext { get; }

    protected StreamingSKResult(SKContext inputContext)
    {
        this.InputSKContext = inputContext;
    }

    public abstract Task<Stream> GetRawStream(CancellationToken cancellationToken = default);

    public abstract IAsyncEnumerable<ITextStreamingResult> GetResults(CancellationToken cancellationToken = default);

    public abstract Task<SKContext> GetOutputSKContextAsync(CancellationToken cancellationToken = default);

    static protected Stream GetStreamFromString(string content)
    {
        var memoryStream = new MemoryStream();
        using (var streamWriter = new StreamWriter(memoryStream))
        {
            streamWriter.Write(content);
            streamWriter.Flush();
        }

        return memoryStream;
    }
}
