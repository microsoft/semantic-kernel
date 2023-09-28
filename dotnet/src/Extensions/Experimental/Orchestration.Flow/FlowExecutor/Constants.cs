// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Orchestration.FlowExecutor;

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

        /// <summary>
        /// Variable name to exit out the of AtLeastOnce or ZeroOrMore loop
        /// </summary>
        public const string ExitLoopName = "ExitLoop";
    }
}
