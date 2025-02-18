// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for interacting with <see cref="PromptExecutionSettings"/>
/// </summary>
public static class PromptExecutionSettingsExtensions
{
    /// <summary>
    /// Property name for model temperature.
    /// </summary>
    private const string Temperature = "temperature";

    /// <summary>
    /// Property name for model TopP.
    /// </summary>
    private const string TopP = "top_p";

    /// <summary>
    /// Property name for model response format.
    /// </summary>
    private const string ResponseFormat = "response_format";

    /// <summary>
    /// Get the temperature property.
    /// </summary>
    /// <param name="executionSettings">Prompt execution settings.</param>
    public static float? GetTemperature(this PromptExecutionSettings executionSettings)
    {
        Verify.NotNull(executionSettings);

        if (executionSettings is OpenAIPromptExecutionSettings openaiSettings)
        {
            return (float?)openaiSettings.Temperature;
        }

        if (executionSettings?.ExtensionData?.TryGetValue(Temperature, out var temperature) ?? false)
        {
            return (float?)temperature;
        }
        return null;
    }

    /// <summary>
    /// Get the TopP property.
    /// </summary>
    /// <param name="executionSettings">Prompt execution settings.</param>
    public static float? GetTopP(this PromptExecutionSettings executionSettings)
    {
        Verify.NotNull(executionSettings);

        if (executionSettings is OpenAIPromptExecutionSettings openaiSettings)
        {
            return (float?)openaiSettings.TopP;
        }

        if (executionSettings?.ExtensionData?.TryGetValue(TopP, out var topP) ?? false)
        {
            return (float?)topP;
        }
        return null;
    }

    /// <summary>
    /// Get the ResponseFormat property.
    /// </summary>
    /// <param name="executionSettings">Prompt execution settings.</param>
    public static bool IsEnableJsonResponse(this PromptExecutionSettings executionSettings)
    {
        Verify.NotNull(executionSettings);

        if (executionSettings is OpenAIPromptExecutionSettings openaiSettings)
        {
            return openaiSettings.ResponseFormat is not null;
        }

        if (executionSettings?.ExtensionData?.TryGetValue(ResponseFormat, out var responseFormat) ?? false)
        {
            return responseFormat is not null;
        }
        return false;
    }
}
