// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SemanticKernel.Connectors.AzureOpenAI.Core;

/// <summary>
/// This class is used to remove duplicate Authorization headers from the request Azure OpenAI Bug.
/// https://github.com/Azure/azure-sdk-for-net/issues/46109 (Remove when beta.2 is released)
/// </summary>
internal sealed class SingleAuthorizationHeaderPolicy : PipelinePolicy
{
    private const string AuthorizationHeaderName = "Authorization";

    public override void Process(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        RemoveDuplicateHeaderValues(message.Request.Headers);

        ProcessNext(message, pipeline, currentIndex);
    }

    public override async ValueTask ProcessAsync(PipelineMessage message, IReadOnlyList<PipelinePolicy> pipeline, int currentIndex)
    {
        RemoveDuplicateHeaderValues(message.Request.Headers);

        await ProcessNextAsync(message, pipeline, currentIndex).ConfigureAwait(false);
    }

    private static void RemoveDuplicateHeaderValues(PipelineRequestHeaders headers)
    {
        if (headers.TryGetValues(AuthorizationHeaderName, out var headerValues)
            && headerValues is not null
#if NET 
            && headerValues.TryGetNonEnumeratedCount(out var count) && count > 1
#else
            && headerValues.Count() > 1
#endif
            )
        {
            headers.Set(AuthorizationHeaderName, headerValues.First());
        }
    }
}
