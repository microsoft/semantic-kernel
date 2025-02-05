// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.ChatCompletion;

public abstract class FallbackEvaluator
{
    public abstract bool ShouldFallbackToNextClient(ShouldFallbackContext context);
}
