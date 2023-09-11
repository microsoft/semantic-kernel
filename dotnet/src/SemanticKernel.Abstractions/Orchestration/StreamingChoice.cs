// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;

public abstract class StreamingChoice : IStreamingChoice
{
    private readonly Stream _rawStream;

    protected StreamingChoice(Stream rawStream)
    {
        this._rawStream = rawStream;
    }

    public virtual Task<Stream> GetRawStreamAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._rawStream);
    }
}
