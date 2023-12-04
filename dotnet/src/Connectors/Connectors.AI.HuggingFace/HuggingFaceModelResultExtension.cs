// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides an extension method for working with Hugging Face model results.
/// </summary>
public static class HuggingFaceModelResultExtension
{
    /// <summary>
    /// Retrieves a typed <see cref="TextGenerationResponse"/> hugging face result from <see cref="ModelResult"/>.
    /// </summary>
    /// <param name="resultBase">The <see cref="ModelResult"/> instance to retrieve the hugging face result from.</param>
    /// <returns>A <see cref="TextGenerationResponse"/> instance containing the hugging face result.</returns>
    public static TextGenerationResponse GetHuggingFaceResult(this ModelResult resultBase)
    {
        return resultBase.GetResult<TextGenerationResponse>();
    }
}
