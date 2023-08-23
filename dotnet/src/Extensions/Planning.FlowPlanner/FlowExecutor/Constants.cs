// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

internal static class Constants
{
    internal static class ActionVariableNames
    {
        /// <summary>
        /// Variable name for the chat history
        /// </summary>
        public const string ChatHistory = "_chatHistory";

        /// <summary>
        /// Variable name for the chat input
        /// </summary>
        public const string ChatInput = "_chatInput";

        /// <summary>
        /// All reserved variable names
        /// </summary>
        public static readonly string[] All = new[] { ChatHistory, ChatInput };
    }

    internal static class ChatSkillVariables
    {
        /// <summary>
        /// Variable name to prompt input
        /// </summary>
        public const string PromptInputName = "PromptInput";

        /// <summary>
        /// Variable value to prompt input
        /// </summary>
        public const string PromptInputValue = "True";
    }
}
