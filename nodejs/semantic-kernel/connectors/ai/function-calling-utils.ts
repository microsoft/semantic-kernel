import { ChatMessageContent } from '../../contents/chat-message-content'
import { FunctionResultContent } from '../../contents/function-result-content'
import { StreamingChatMessageContent } from '../../contents/streaming-chat-message-content'
import { AuthorRole } from '../../contents/utils/author-role'
import { KernelFunctionMetadata } from '../../functions/kernel-function-metadata'
import { Kernel } from '../../kernel'
import { PromptExecutionSettings } from '../../services/ai-service-client-base'
import { FunctionCallChoiceConfiguration } from './function-call-choice-configuration'
import { FunctionChoiceType } from './function-choice-type'

/**
 * Update the settings from a FunctionChoiceConfiguration.
 *
 * @param functionChoiceConfiguration - The function choice configuration
 * @param settings - The prompt execution settings to update
 * @param type - The function choice type
 */
export function updateSettingsFromFunctionCallConfiguration(
  functionChoiceConfiguration: FunctionCallChoiceConfiguration,
  settings: PromptExecutionSettings,
  type: FunctionChoiceType
): void {
  const settingsWithTools = settings as any

  if (
    functionChoiceConfiguration.availableFunctions &&
    'toolChoice' in settingsWithTools &&
    'tools' in settingsWithTools
  ) {
    settingsWithTools.toolChoice = type
    settingsWithTools.tools = functionChoiceConfiguration.availableFunctions.map((f) =>
      kernelFunctionMetadataToFunctionCallFormat(f)
    )
  }
}

/**
 * Convert the kernel function metadata to function calling format.
 *
 * @param metadata - The kernel function metadata
 * @returns The function call format object
 */
export function kernelFunctionMetadataToFunctionCallFormat(metadata: KernelFunctionMetadata): Record<string, any> {
  const includedParams = metadata.parameters.filter((p) => p.includeInFunctionChoices !== false)
  const requiredParams = includedParams.filter((p) => p.isRequired)

  return {
    type: 'function',
    function: {
      name: metadata.fullyQualifiedName,
      description: metadata.description || '',
      parameters: {
        type: 'object',
        properties: Object.fromEntries(includedParams.map((param) => [param.name, param.schemaData])),
        required: requiredParams.map((p) => p.name),
      },
    },
  }
}

/**
 * Convert the kernel function metadata to response function calling format.
 *
 * @param metadata - The kernel function metadata
 * @returns The response function call format object
 */
export function kernelFunctionMetadataToResponseFunctionCallFormat(
  metadata: KernelFunctionMetadata
): Record<string, any> {
  const includedParams = metadata.parameters.filter((p) => p.includeInFunctionChoices !== false)
  const requiredParams = includedParams.filter((p) => p.isRequired)

  return {
    type: 'function',
    name: metadata.fullyQualifiedName,
    description: metadata.description || '',
    parameters: {
      type: 'object',
      properties: Object.fromEntries(includedParams.map((param) => [param.name, param.schemaData])),
      required: requiredParams.map((p) => p.name),
    },
  }
}

/**
 * Combine multiple filter dictionaries with list values into one dictionary.
 * This method ensures unique values while preserving order.
 *
 * @param dicts - The filter dictionaries to combine
 * @returns The combined filter dictionary
 */
export function combineFilterDicts(...dicts: Record<string, string[]>[]): Record<string, string[]> {
  const combinedFilters: Record<string, string[]> = {}

  // Get all unique keys
  const keys = new Set<string>()
  for (const dict of dicts) {
    for (const key of Object.keys(dict)) {
      keys.add(key)
    }
  }

  for (const key of keys) {
    const combinedFunctions = new Map<string, null>()

    for (const dict of dicts) {
      if (key in dict) {
        const value = dict[key]
        if (!Array.isArray(value)) {
          throw new Error(`Values for filter key '${key}' are not lists.`)
        }
        for (const item of value) {
          combinedFunctions.set(item, null)
        }
      }
    }

    combinedFilters[key] = Array.from(combinedFunctions.keys())
  }

  return combinedFilters
}

/**
 * Combine multiple function result content types to one chat message content type.
 * This method combines the FunctionResultContent items from separate ChatMessageContent messages,
 * and is used in the event that the `terminate = true` condition is met.
 *
 * @param messages - The list of chat message content types
 * @returns The combined chat message content
 */
export function mergeFunctionResults(messages: ChatMessageContent[]): ChatMessageContent[] {
  const items: FunctionResultContent[] = []

  for (const message of messages) {
    for (const item of message.items) {
      if (item instanceof FunctionResultContent) {
        items.push(item)
      }
    }
  }

  return [
    new ChatMessageContent({
      role: AuthorRole.TOOL,
      items: items as any,
    }),
  ]
}

/**
 * Combine multiple streaming function result content types to one streaming chat message content type.
 * This method combines the FunctionResultContent items from separate StreamingChatMessageContent messages,
 * and is used in the event that the `terminate = true` condition is met.
 *
 * @param messages - The list of streaming chat message content types
 * @param aiModelId - The AI model ID
 * @param functionInvokeAttempt - The function invoke attempt
 * @returns The combined streaming chat message content
 */
export function mergeStreamingFunctionResults(
  messages: (ChatMessageContent | StreamingChatMessageContent)[],
  aiModelId?: string,
  functionInvokeAttempt?: number
): StreamingChatMessageContent[] {
  const items: FunctionResultContent[] = []

  for (const message of messages) {
    for (const item of message.items) {
      if (item instanceof FunctionResultContent) {
        items.push(item)
      }
    }
  }

  return [
    new StreamingChatMessageContent({
      role: AuthorRole.TOOL,
      items: items as any,
      choiceIndex: 0,
      aiModelId,
      functionInvokeAttempt,
    }),
  ]
}

/**
 * Prepare settings for the service.
 *
 * @param settings - Prompt execution settings
 * @param settingsClass - The settings class constructor
 * @param updateSettingsCallback - The callback to update the settings
 * @param kernel - Kernel instance
 * @returns PromptExecutionSettings of type settingsClass
 */
export function prepareSettingsForFunctionCalling<T extends PromptExecutionSettings>(
  settings: PromptExecutionSettings,
  settingsClass: new (...args: any[]) => T,
  updateSettingsCallback: (...args: any[]) => void,
  kernel: Kernel
): T {
  // Deep copy the settings
  settings = JSON.parse(JSON.stringify(settings))

  if (!(settings instanceof settingsClass)) {
    // Try to use fromPromptExecutionSettings if available
    if (typeof (settingsClass as any).fromPromptExecutionSettings === 'function') {
      settings = (settingsClass as any).fromPromptExecutionSettings(settings)
    } else {
      settings = new settingsClass(settings)
    }
  }

  const functionChoiceBehavior = (settings as any).functionChoiceBehavior

  if (functionChoiceBehavior) {
    // Configure the function choice behavior into the settings object
    functionChoiceBehavior.configure({
      kernel,
      updateSettingsCallback,
      settings,
    })
  }

  return settings as T
}
