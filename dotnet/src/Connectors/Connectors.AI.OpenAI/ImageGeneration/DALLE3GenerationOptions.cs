// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

/// <summary>
/// Image Generation options for DALL-E 3
/// </summary>
public class DALLE3GenerationOptions
{
    /// <summary>
    /// The quality of the image that will be generated. `hd` creates images with finer details and greater consistency across the image. Defaults to `standard`.
    /// </summary>
    public string Quality { get; set; } = "standard";

    /// <summary>
    /// The style of the generated images. Must be one of `vivid` or `natural`. Defaults to vivid
    /// </summary>
    public string Style { get; set; } = "vivid";
}
