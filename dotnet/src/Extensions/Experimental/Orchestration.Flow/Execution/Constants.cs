// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

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

    internal static class ChatPluginVariables
    {
        /// <summary>
        /// Variable name to prompt input
        /// </summary>
        public const string PromptInputName = "PromptInput";

        /// <summary>
        /// Variable name to exit out the of AtLeastOnce or ZeroOrMore loop
        /// </summary>
        public const string ExitLoopName = "ExitLoop";

        /// <summary>
        /// Variable name to force the next iteration of the of AtLeastOnce or ZeroOrMore loop
        /// </summary>
        public const string ContinueLoopName = "ContinueLoop";

        /// <summary>
        /// Default variable value
        /// </summary>
        public const string DefaultValue = "True";

        /// <summary>
        /// The variables that change the default flow
        /// </summary>
        public static readonly string[] ControlVariables = new[] { PromptInputName, ExitLoopName, ContinueLoopName };
    }
}
