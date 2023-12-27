// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

public interface IPromptFilter
{
    void OnPromptRendering(PromptRenderingContext context);

    void OnPromptRendered(PromptRenderedContext context);
}
