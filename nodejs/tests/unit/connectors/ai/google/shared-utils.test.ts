import { FunctionChoiceType } from '../../../../../semantic-kernel/connectors/ai/function-choice-type'
import {
  collapseFunctionCallResultsInChatHistory,
  filterSystemMessage,
  formatGeminiFunctionNameToKernelFunctionFullyQualifiedName,
  FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE,
  GEMINI_FUNCTION_NAME_SEPARATOR,
} from '../../../../../semantic-kernel/connectors/ai/google/shared-utils'
import { ChatHistory } from '../../../../../semantic-kernel/contents/chat-history'
import { ChatMessageContent } from '../../../../../semantic-kernel/contents/chat-message-content'
import { FunctionCallContent } from '../../../../../semantic-kernel/contents/function-call-content'
import { FunctionResultContent } from '../../../../../semantic-kernel/contents/function-result-content'
import { AuthorRole } from '../../../../../semantic-kernel/contents/utils/author-role'
import { ServiceInvalidRequestError } from '../../../../../semantic-kernel/exceptions/service-exceptions'

describe('shared-utils', () => {
  describe('filterSystemMessage', () => {
    it('should return system message content when single system message exists', () => {
      const chatHistory = new ChatHistory()
      chatHistory.addSystemMessage('System message')
      chatHistory.addUserMessage('User message')

      const result = filterSystemMessage(chatHistory)

      expect(result).toBe('System message')
    })

    it('should return null when no system message exists', () => {
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('User message')

      const result = filterSystemMessage(chatHistory)

      expect(result).toBeNull()
    })

    it('should throw error when multiple system messages exist', () => {
      const chatHistory = new ChatHistory()
      chatHistory.addSystemMessage('System message 1')
      chatHistory.addSystemMessage('System message 2')

      expect(() => filterSystemMessage(chatHistory)).toThrow(ServiceInvalidRequestError)
      expect(() => filterSystemMessage(chatHistory)).toThrow(
        'Multiple system messages in chat history. Only one system message is expected.'
      )
    })
  })

  describe('FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE', () => {
    it('should contain all function choice types', () => {
      expect(FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[FunctionChoiceType.AUTO]).toBeDefined()
      expect(FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[FunctionChoiceType.NONE]).toBeDefined()
      expect(FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[FunctionChoiceType.REQUIRED]).toBeDefined()
    })

    it('should map AUTO to AUTO', () => {
      expect(FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[FunctionChoiceType.AUTO]).toBe('AUTO')
    })

    it('should map NONE to NONE', () => {
      expect(FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[FunctionChoiceType.NONE]).toBe('NONE')
    })

    it('should map REQUIRED to ANY', () => {
      expect(FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[FunctionChoiceType.REQUIRED]).toBe('ANY')
    })
  })

  describe('formatGeminiFunctionNameToKernelFunctionFullyQualifiedName', () => {
    it('should convert function name containing separator to fully qualified name', () => {
      const geminiFunctionName = `plugin${GEMINI_FUNCTION_NAME_SEPARATOR}function`

      const result = formatGeminiFunctionNameToKernelFunctionFullyQualifiedName(geminiFunctionName)

      expect(result).toBe('plugin-function')
    })

    it('should return function name as-is when separator not present', () => {
      const geminiFunctionName = 'function'

      const result = formatGeminiFunctionNameToKernelFunctionFullyQualifiedName(geminiFunctionName)

      expect(result).toBe('function')
    })
  })

  describe('collapseFunctionCallResultsInChatHistory', () => {
    it('should collapse consecutive tool messages into single message', () => {
      const chatHistory = new ChatHistory()
      chatHistory.messages.push(
        new ChatMessageContent({
          role: AuthorRole.ASSISTANT,
          items: [
            new FunctionCallContent({ id: 'function1', functionName: 'function1' }),
            new FunctionCallContent({ id: 'function2', functionName: 'function2' }),
          ],
        }),
        // The following two messages should be collapsed into a single message
        new ChatMessageContent({
          role: AuthorRole.TOOL,
          items: [new FunctionResultContent({ id: 'function1', functionName: 'function1', result: 'result1' })],
        }),
        new ChatMessageContent({
          role: AuthorRole.TOOL,
          items: [new FunctionResultContent({ id: 'function2', functionName: 'function2', result: 'result2' })],
        }),
        new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'Assistant message' }),
        new ChatMessageContent({ role: AuthorRole.USER, content: 'User message' }),
        new ChatMessageContent({
          role: AuthorRole.ASSISTANT,
          items: [new FunctionCallContent({ id: 'function3', functionName: 'function3' })],
        }),
        new ChatMessageContent({
          role: AuthorRole.TOOL,
          items: [new FunctionResultContent({ id: 'function3', functionName: 'function3', result: 'result3' })],
        }),
        new ChatMessageContent({ role: AuthorRole.ASSISTANT, content: 'Assistant message' })
      )

      expect(chatHistory.messages).toHaveLength(8)

      collapseFunctionCallResultsInChatHistory(chatHistory)

      expect(chatHistory.messages).toHaveLength(7)
      expect(chatHistory.messages[1].items).toHaveLength(2)
    })

    it('should handle empty chat history', () => {
      const chatHistory = new ChatHistory()

      expect(() => collapseFunctionCallResultsInChatHistory(chatHistory)).not.toThrow()
      expect(chatHistory.messages).toHaveLength(0)
    })

    it('should not modify chat history with no consecutive tool messages', () => {
      const chatHistory = new ChatHistory()
      chatHistory.addUserMessage('User message 1')
      chatHistory.addAssistantMessage('Assistant message 1')
      chatHistory.addUserMessage('User message 2')

      expect(chatHistory.messages).toHaveLength(3)

      collapseFunctionCallResultsInChatHistory(chatHistory)

      expect(chatHistory.messages).toHaveLength(3)
    })
  })
})
