// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;

public abstract record StreamingSKResult
{
    public SKContext InputContext { get; }

    protected StreamingSKResult(SKContext inputContext)
    {
        this.InputContext = inputContext;
    }

    public abstract IEnumerable<IStreamingChoice> GetChoices(CancellationToken cancellationToken = default);

    public abstract Task<IEnumerable<SKContext>> GetChoiceContextsAsync(CancellationToken cancellationToken = default);

    public static Stream GetStreamFromString(string content)
    {
        var memoryStream = new MemoryStream();
        using (var streamWriter = new StreamWriter(memoryStream))
        {
            streamWriter.Write(content);
            streamWriter.Flush();
        }

        memoryStream.Position = 0;
        return memoryStream;
    }

    public static string GetStringFromStream(Stream stream)
    {
        using var streamReader = new StreamReader(stream);
        return streamReader.ReadToEnd();
    }
}
