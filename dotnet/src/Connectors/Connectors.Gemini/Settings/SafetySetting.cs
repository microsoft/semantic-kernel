#region HEADER
// Copyright (c) Microsoft. All rights reserved.
#endregion

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Settings;

public sealed class SafetySetting
{
    /// <summary>
    /// Initializes a new instance of the Gemini <see cref="SafetySetting"/> class.
    /// </summary>
    /// <param name="category">Category of safety</param>
    /// <param name="threshold">Value</param>
    public SafetySetting(string category, string threshold)
    {
        this.Category = category;
        this.Threshold = threshold;
    }

    /// <summary>
    /// Gets or sets the safety category.
    /// </summary>
    public string Category { get; set; }

    /// <summary>
    /// Gets or sets the safety threshold.
    /// </summary>
    public string Threshold { get; set; }
}

public static class SafetyCategory
{
    /// <summary>
    /// Category is unspecified.
    /// </summary>
    public const string HarmCategoryUnspecified = "HARM_CATEGORY_UNSPECIFIED";

    /// <summary>
    /// Contains negative or harmful comments targeting identity and/or protected attributes.
    /// </summary>
    public const string HarmCategoryDerogatory = "HARM_CATEGORY_DEROGATORY";

    /// <summary>
    /// Includes content that is rude, disrespectful, or profane.
    /// </summary>
    public const string HarmCategoryToxicity = "HARM_CATEGORY_TOXICITY";

    /// <summary>
    /// Describes scenarios depicting violence against an individual or group, or general descriptions of gore.
    /// </summary>
    public const string HarmCategoryViolence = "HARM_CATEGORY_VIOLENCE";

    /// <summary>
    /// Contains references to sexual acts or other lewd content.
    /// </summary>
    public const string HarmCategorySexual = "HARM_CATEGORY_SEXUAL";

    /// <summary>
    /// Contains unchecked medical advice.
    /// </summary>
    public const string HarmCategoryMedical = "HARM_CATEGORY_MEDICAL";

    /// <summary>
    /// Includes content that promotes, facilitates, or encourages harmful acts.
    /// </summary>
    public const string HarmCategoryDangerous = "HARM_CATEGORY_DANGEROUS";

    /// <summary>
    /// Consists of harassment content.
    /// </summary>
    public const string HarmCategoryHarassment = "HARM_CATEGORY_HARASSMENT";

    /// <summary>
    /// Contains sexually explicit content.
    /// </summary>
    public const string HarmCategorySexuallyExplicit = "HARM_CATEGORY_SEXUALLY_EXPLICIT";

    /// <summary>
    /// Contains dangerous content.
    /// </summary>
    public const string HarmCategoryDangerousContent = "HARM_CATEGORY_DANGEROUS_CONTENT";
}

public static class SafetyThreshold
{
    /// <summary>
    /// Always show regardless of probability of unsafe content.
    /// </summary>
    public const string BlockNone = "BLOCK_NONE";

    /// <summary>
    /// Block when high probability of unsafe content.
    /// </summary>
    public const string BlockOnlyHigh = "BLOCK_ONLY_HIGH";

    /// <summary>
    /// Block when medium or high probability of unsafe content.
    /// </summary>
    public const string BlockMediumAndAbove = "BLOCK_MEDIUM_AND_ABOVE";

    /// <summary>
    /// Block when low, medium or high probability of unsafe content.
    /// </summary>
    public const string BlockLowAndAbove = "BLOCK_LOW_AND_ABOVE";

    /// <summary>
    /// Threshold is unspecified, block using default threshold.
    /// </summary>
    public const string HarmBlockThresholdUnspecified = "HARM_BLOCK_THRESHOLD_UNSPECIFIED";
}
