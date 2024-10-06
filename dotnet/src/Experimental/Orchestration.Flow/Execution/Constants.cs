<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> origin/main
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

internal static class Constants
{
    /// <summary>
    /// The function name to indicate stop execution and prompt user
    /// </summary>
    public const string StopAndPromptFunctionName = "StopAndPrompt";

    /// <summary>
    /// The parameter name of StopAndPrompt function
    /// </summary>
    public const string StopAndPromptParameterName = "prompt";

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
        public static readonly string[] All = [ChatHistory, ChatInput];
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
        public static readonly string[] All = new[] { ChatHistory, ChatInput };
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
        public static readonly string[] All = new[] { ChatHistory, ChatInput };
>>>>>>> origin/main
>>>>>>> Stashed changes
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
        /// Variable name to terminate the flow
        /// </summary>
        public const string StopFlowName = "StopFlow";

        /// <summary>
        /// Default variable value
        /// </summary>
        public const string DefaultValue = "True";

        /// <summary>
        /// The variables that change the default flow
        /// </summary>
        public static readonly string[] ControlVariables = [PromptInputName, ExitLoopName, ContinueLoopName, StopFlowName];
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
        public static readonly string[] ControlVariables = new[] { PromptInputName, ExitLoopName, ContinueLoopName, StopFlowName };
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
        public static readonly string[] ControlVariables = new[] { PromptInputName, ExitLoopName, ContinueLoopName, StopFlowName };
>>>>>>> origin/main
>>>>>>> Stashed changes
    }
}
