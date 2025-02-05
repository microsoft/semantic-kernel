// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.ChatCompletion;

public sealed class CustomFallbackEvaluator : FallbackEvaluator
{
    private readonly Func<ShouldFallbackContext, bool> _predicate;

    public CustomFallbackEvaluator(Func<ShouldFallbackContext, bool> predicate)
    {
        this._predicate = predicate;
    }

    public override bool ShouldFallbackToNextClient(ShouldFallbackContext context)
    {
        return this._predicate(context);
    }
}
