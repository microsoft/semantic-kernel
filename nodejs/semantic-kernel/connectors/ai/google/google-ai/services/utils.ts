import { ChatMessageContent } from '../../../../../contents/chat-message-content'
import { FunctionCallContent } from '../../../../../contents/function-call-content'
import { FunctionResultContent } from '../../../../../contents/function-result-content'
import { ImageContent } from '../../../../../contents/image-content'
import { TextContent } from '../../../../../contents/text-content'
import { FinishReason } from '../../../../../contents/utils/finish-reason'
import { ServiceInvalidRequestError } from '../../../../../exceptions/service-exceptions'
import { KernelFunctionMetadata } from '../../../../../functions/kernel-function-metadata'
import { PromptExecutionSettings } from '../../../../../services/ai-service-client-base'
import { FunctionChoiceType } from '../../../function-choice-type'
import {
  FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE,
  GEMINI_FUNCTION_NAME_SEPARATOR,
} from '../../shared-utils'
import { GoogleAIChatPromptExecutionSettings } from '../google-ai-prompt-execution-settings'

// Google AI SDK types
export enum GoogleAIFinishReason {
  STOP = 'STOP',
  MAX_TOKENS = 'MAX_TOKENS',
  SAFETY = 'SAFETY',
  RECITATION = 'RECITATION',
  OTHER = 'OTHER',
  BLOCKLIST = 'BLOCKLIST',
  PROHIBITED_CONTENT = 'PROHIBITED_CONTENT',
  SPII = 'SPII',
  MALFORMED_FUNCTION_CALL = 'MALFORMED_FUNCTION_CALL',
}

export interface Part {
  text?: string
  functionCall?: {
    name: string
    args: Record<string, any>
  }
  functionResponse?: {
    name: string
    response: any
  }
  inlineData?: {
    mimeType: string
    data: string | Uint8Array
  }
}

export interface FunctionCallChoiceConfiguration {
  availableFunctions?: KernelFunctionMetadata[]
}

/**
 * Convert a Google AI FinishReason to a Semantic Kernel FinishReason.
 *
 * This is best effort and may not cover all cases as the enums are not identical.
 *
 * @param finishReason - The Google AI finish reason
 * @returns The Semantic Kernel finish reason, or null if no mapping exists
 */
export function finishReasonFromGoogleAIToSemanticKernel(
  finishReason: GoogleAIFinishReason | string | null | undefined
): FinishReason | null {
  if (!finishReason) {
    return null
  }

  if (finishReason === GoogleAIFinishReason.STOP || finishReason === 'STOP') {
    return FinishReason.STOP
  }

  if (finishReason === GoogleAIFinishReason.MAX_TOKENS || finishReason === 'MAX_TOKENS') {
    return FinishReason.LENGTH
  }

  if (finishReason === GoogleAIFinishReason.SAFETY || finishReason === 'SAFETY') {
    return FinishReason.CONTENT_FILTER
  }

  return null
}

/**
 * Format a user message to the expected object for the client.
 *
 * @param message - The user message
 * @returns The formatted user message as a list of parts
 */
export function formatUserMessage(message: ChatMessageContent): Part[] {
  const parts: Part[] = []

  for (const item of message.items) {
    if (item instanceof TextContent) {
      parts.push({ text: item.text })
    } else if (item instanceof ImageContent) {
      parts.push(createImagePart(item))
    } else {
      throw new ServiceInvalidRequestError(
        `Unsupported item type in User message while formatting chat history for Google AI Inference: ${item.constructor.name}`
      )
    }
  }

  return parts
}

/**
 * Format an assistant message to the expected object for the client.
 *
 * @param message - The assistant message
 * @returns The formatted assistant message as a list of parts
 */
export function formatAssistantMessage(message: ChatMessageContent): Part[] {
  const parts: Part[] = []

  for (const item of message.items) {
    if (item instanceof TextContent) {
      if (item.text) {
        parts.push({ text: item.text })
      }
    } else if (item instanceof FunctionCallContent) {
      const args = typeof item.arguments === 'string' ? JSON.parse(item.arguments) : item.arguments

      parts.push({
        functionCall: {
          name: item.name || '',
          args: args || {},
        },
      })
    } else if (item instanceof ImageContent) {
      parts.push(createImagePart(item))
    } else {
      throw new ServiceInvalidRequestError(
        `Unsupported item type in Assistant message while formatting chat history for Google AI Inference: ${item.constructor.name}`
      )
    }
  }

  return parts
}

/**
 * Format a tool message to the expected object for the client.
 *
 * @param message - The tool message
 * @returns The formatted tool message
 */
export function formatToolMessage(message: ChatMessageContent): Part[] {
  const parts: Part[] = []

  for (const item of message.items) {
    if (item instanceof FunctionResultContent) {
      const geminiFunctionName = item.customFullyQualifiedName(GEMINI_FUNCTION_NAME_SEPARATOR)

      parts.push({
        functionResponse: {
          name: geminiFunctionName,
          response: {
            content: String(item.result),
          },
        },
      })
    }
  }

  return parts
}

/**
 * Convert the kernel function metadata to function calling format.
 *
 * @param metadata - The kernel function metadata
 * @returns The function calling format
 */
export function kernelFunctionMetadataToGoogleAIFunctionCallFormat(
  metadata: KernelFunctionMetadata
): Record<string, any> {
  const result: Record<string, any> = {
    name: metadata.customFullyQualifiedName(GEMINI_FUNCTION_NAME_SEPARATOR),
    description: metadata.description || '',
  }

  if (metadata.parameters && metadata.parameters.length > 0) {
    const properties: Record<string, any> = {}
    const required: string[] = []

    for (const param of metadata.parameters) {
      properties[param.name] = param.schemaData || {}
      if (param.isRequired) {
        required.push(param.name)
      }
    }

    result.parameters = {
      type: 'object',
      properties,
      required,
    }
  } else {
    result.parameters = null
  }

  return result
}

/**
 * Update the settings from a FunctionChoiceConfiguration.
 *
 * @param functionChoiceConfiguration - The function choice configuration
 * @param settings - The prompt execution settings
 * @param type - The function choice type
 */
export function updateSettingsFromFunctionChoiceConfiguration(
  functionChoiceConfiguration: FunctionCallChoiceConfiguration,
  settings: PromptExecutionSettings,
  type: FunctionChoiceType
): void {
  if (!(settings instanceof GoogleAIChatPromptExecutionSettings)) {
    throw new Error('Settings must be an instance of GoogleAIChatPromptExecutionSettings')
  }

  if (functionChoiceConfiguration.availableFunctions && functionChoiceConfiguration.availableFunctions.length > 0) {
    settings.toolConfig = {
      function_calling_config: {
        mode: FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[type],
      },
    }

    settings.tools = [
      {
        function_declarations: functionChoiceConfiguration.availableFunctions.map((f) =>
          kernelFunctionMetadataToGoogleAIFunctionCallFormat(f)
        ),
      },
    ]
  }
}

/**
 * Create an image part from ImageContent.
 *
 * @param imageContent - The image content
 * @returns The image part
 * @private
 */
function createImagePart(imageContent: ImageContent): Part {
  if (imageContent.dataUri) {
    return {
      inlineData: {
        mimeType: imageContent.mimeType || 'image/png',
        data: imageContent.data || new Uint8Array(),
      },
    }
  }

  // The Google AI API doesn't support images from arbitrary URIs:
  // https://github.com/google-gemini/generative-ai-python/issues/357
  throw new ServiceInvalidRequestError(
    'ImageContent without data_uri in User message while formatting chat history for Google AI'
  )
}
