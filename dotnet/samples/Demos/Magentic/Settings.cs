// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace Magentic;

internal static class Settings
{
    private const string AzureOpenAISectionName = "AzureOpenAI";
    private const string AzureOpenAITextToImageSectionName = "AzureOpenAITextToImage";
    private const string OpenAISectionName = "OpenAI";

    public static ChatCompletionSettings GetChatCompletionSettings(this IConfigurationRoot configuration)
    {
        return
            configuration.GetSection(AzureOpenAISectionName).Get<ChatCompletionSettings>() ??
            throw new InvalidDataException($"Unable to read settings: {AzureOpenAISectionName}");
    }

    public static TextToImageSettings GetTextToImageSettings(this IConfigurationRoot configuration)
    {
        return
            configuration.GetSection(AzureOpenAITextToImageSectionName).Get<TextToImageSettings>() ??
            throw new InvalidDataException($"Unable to read settings: {AzureOpenAITextToImageSectionName}");
    }

    public static OpenAISettings GetOpenAISettings(this IConfigurationRoot configuration)
    {
        return
            configuration.GetSection(OpenAISectionName).Get<OpenAISettings>() ??
            throw new InvalidDataException($"Unable to read settings: {OpenAISectionName}");
    }

    public sealed class ChatCompletionSettings
    {
        public string Endpoint { get; set; } = string.Empty;
        public string DeploymentName { get; set; } = string.Empty;
    }

    public sealed class OpenAISettings
    {
        public string ApiKey { get; set; } = string.Empty;
        public string ChatModel { get; set; } = string.Empty;
        public string ImageModel { get; set; } = string.Empty;
        public string ReasoningModel { get; set; } = string.Empty;
        public string SearchModel { get; set; } = string.Empty;
    }

    public sealed class TextToImageSettings
    {
        public string Endpoint { get; set; } = string.Empty;
        public string DeploymentName { get; set; } = string.Empty;
    }
}
