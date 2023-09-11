// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;

public interface IStreamingChoice
{
    public Task<Stream> GetRawStreamAsync(CancellationToken cancellationToken = default);
}
