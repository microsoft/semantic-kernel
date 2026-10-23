import { DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR } from '../../../const'
import { ChatHistory } from '../../../contents/chat-history'
import { AuthorRole } from '../../../contents/utils/author-role'
import { ServiceInvalidRequestError } from '../../../exceptions/service-exceptions'
import { FunctionChoiceType } from '../function-choice-type'

/**
 * Filter the first system message from the chat history.
 * If there are multiple system messages, throw an error.
 * If there are no system messages, return null.
 */
export function filterSystemMessage(chatHistory: ChatHistory): string | null {
  const systemMessages = chatHistory.messages.filter((message) => message.role === AuthorRole.SYSTEM)
  if (systemMessages.length > 1) {
    throw new ServiceInvalidRequestError(
      'Multiple system messages in chat history. Only one system message is expected.'
    )
  }
  if (systemMessages.length === 1) {
    return systemMessages[0].content
  }
  return null
}

export const FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE: Record<FunctionChoiceType, string> = {
  [FunctionChoiceType.AUTO]: 'AUTO',
  [FunctionChoiceType.NONE]: 'NONE',
  [FunctionChoiceType.REQUIRED]: 'ANY',
}

// The separator used in the fully qualified name of the function instead of the default "-" separator.
// This is required since Gemini doesn't work well with "-" in the function name.
// https://ai.google.dev/gemini-api/docs/function-calling#function_declarations
// Using double underscore to avoid situations where the function name already contains a single underscore.
export const GEMINI_FUNCTION_NAME_SEPARATOR = '__'

/**
 * Format the Gemini function name to the kernel function fully qualified name.
 */
export function formatGeminiFunctionNameToKernelFunctionFullyQualifiedName(geminiFunctionName: string): string {
  if (geminiFunctionName.includes(GEMINI_FUNCTION_NAME_SEPARATOR)) {
    const [pluginName, functionName] = geminiFunctionName.split(GEMINI_FUNCTION_NAME_SEPARATOR, 2)
    return pluginName + DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR + functionName
  }
  return geminiFunctionName
}

/**
 * Collapse the results of parallel function calls in the chat history into a single Tool message.
 * The Gemini API expects the results of parallel function calls to be contained in a single message to be returned.
 */
export function collapseFunctionCallResultsInChatHistory(chatHistory: ChatHistory): void {
  if (!chatHistory.messages || chatHistory.messages.length === 0) {
    return
  }

  let currentIdx = 1
  while (currentIdx < chatHistory.messages.length) {
    const previousMessage = chatHistory.messages[currentIdx - 1]
    const currentMessage = chatHistory.messages[currentIdx]
    if (previousMessage.role === AuthorRole.TOOL && currentMessage.role === AuthorRole.TOOL) {
      previousMessage.items.push(...currentMessage.items)
      chatHistory.removeMessage(currentMessage)
    } else {
      currentIdx += 1
    }
  }
}
