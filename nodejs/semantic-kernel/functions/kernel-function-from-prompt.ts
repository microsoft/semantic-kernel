import { PromptExecutionSettings } from '../connectors/ai/prompt-execution-settings'
import { FunctionInvocationContext } from '../filters/functions/function-invocation-context'
import { KERNEL_TEMPLATE_FORMAT_NAME, TemplateFormatTypes } from '../prompt-template/const'
import { PromptTemplateBase } from '../prompt-template/prompt-template-base'
import { PromptTemplateConfig } from '../prompt-template/prompt-template-config'
import { TEMPLATE_FORMAT_MAP } from '../prompt-template/template-format-map'
import { createDefaultLogger } from '../utils/logger'
import { KernelFunction } from './kernel-function'
import { KernelFunctionMetadata } from './kernel-function-metadata'
import { KernelParameterMetadata } from './kernel-parameter-metadata'

const logger = createDefaultLogger('KernelFunctionFromPrompt')

const PROMPT_RETURN_PARAM: KernelParameterMetadata = new KernelParameterMetadata({
  name: 'return',
  description: 'The completion result',
  defaultValue: null,
  type: 'FunctionResult',
  isRequired: true,
})

/**
 * Options for creating a KernelFunctionFromPrompt.
 */
export interface KernelFunctionFromPromptOptions {
  functionName: string
  pluginName?: string
  description?: string
  prompt?: string
  templateFormat?: TemplateFormatTypes
  promptTemplate?: PromptTemplateBase
  promptTemplateConfig?: PromptTemplateConfig
  promptExecutionSettings?: PromptExecutionSettings | PromptExecutionSettings[] | Map<string, PromptExecutionSettings>
}

/**
 * Semantic Kernel Function from a prompt.
 */
export class KernelFunctionFromPrompt extends KernelFunction {
  /**
   * The prompt template.
   */
  public promptTemplate: PromptTemplateBase

  /**
   * The prompt execution settings.
   */
  public promptExecutionSettings: Map<string, PromptExecutionSettings>

  /**
   * Creates a new KernelFunctionFromPrompt instance.
   * @param options - The options for creating the function.
   */
  constructor(options: KernelFunctionFromPromptOptions) {
    const {
      functionName,
      pluginName,
      description,
      prompt,
      templateFormat = KERNEL_TEMPLATE_FORMAT_NAME,
      promptTemplate,
      promptTemplateConfig,
      promptExecutionSettings,
    } = options

    // Validate that we have a prompt source
    if (!prompt && !promptTemplateConfig && !promptTemplate) {
      throw new Error(
        'The prompt cannot be empty, must be supplied directly, through promptTemplateConfig or in the promptTemplate.'
      )
    }

    // Log warnings if conflicting parameters are provided
    if (prompt && promptTemplateConfig && promptTemplateConfig.template !== prompt) {
      logger.warn(
        `Prompt (${prompt}) and PromptTemplateConfig (${promptTemplateConfig.template}) both supplied, ` +
          'using the template in PromptTemplateConfig, ignoring prompt.'
      )
    }
    if (templateFormat && promptTemplateConfig && promptTemplateConfig.templateFormat !== templateFormat) {
      logger.warn(
        `Template (${templateFormat}) and PromptTemplateConfig (${promptTemplateConfig.templateFormat}) ` +
          'both supplied, using the template format in PromptTemplateConfig, ignoring template.'
      )
    }

    // Create prompt template if not provided
    let finalPromptTemplate = promptTemplate
    if (!finalPromptTemplate) {
      let finalConfig = promptTemplateConfig
      if (!finalConfig) {
        // Create config from prompt
        finalConfig = new PromptTemplateConfig({
          name: functionName,
          description,
          template: prompt!,
          templateFormat,
        })
      } else if (!finalConfig.template) {
        finalConfig.template = prompt!
      }

      // Create template from format map
      const TemplateClass = TEMPLATE_FORMAT_MAP[finalConfig.templateFormat]
      if (!TemplateClass) {
        throw new Error(`Unknown template format: ${finalConfig.templateFormat}`)
      }
      finalPromptTemplate = new TemplateClass(finalConfig)
    }

    // Create metadata
    let metadata: KernelFunctionMetadata
    try {
      metadata = new KernelFunctionMetadata({
        name: functionName,
        pluginName,
        description: description || '',
        parameters: finalPromptTemplate.promptTemplateConfig.getKernelParameterMetadata(),
        isPrompt: true,
        isAsynchronous: true,
        returnParameter: PROMPT_RETURN_PARAM,
      })
    } catch (exc) {
      throw new Error(`Failed to create KernelFunctionMetadata: ${exc}`, { cause: exc })
    }

    super(metadata)

    this.promptTemplate = finalPromptTemplate

    // Handle prompt execution settings
    this.promptExecutionSettings = new Map()

    // Use execution settings from promptTemplateConfig if not explicitly provided
    let finalExecutionSettings = promptExecutionSettings
    if (!finalExecutionSettings && finalPromptTemplate.promptTemplateConfig.executionSettings) {
      finalExecutionSettings = finalPromptTemplate.promptTemplateConfig.executionSettings
    }

    if (finalExecutionSettings) {
      if (finalExecutionSettings instanceof Map) {
        this.promptExecutionSettings = finalExecutionSettings
      } else if (Array.isArray(finalExecutionSettings)) {
        for (const setting of finalExecutionSettings) {
          const serviceName = (setting as any).service_id || setting.serviceId || 'default'
          this.promptExecutionSettings.set(serviceName, setting)
        }
      } else {
        const serviceName = (finalExecutionSettings as any).service_id || finalExecutionSettings.serviceId || 'default'
        this.promptExecutionSettings.set(serviceName, finalExecutionSettings)
      }
    }
  }

  /**
   * Internal invoke method implementation.
   * @param context - The function invocation context.
   */
  protected async _invokeInternal(context: FunctionInvocationContext): Promise<void> {
    const { FunctionResult } = await import('./function-result.js')
    const { ChatHistory } = await import('../contents/chat-history.js')

    // Render the prompt
    const renderedPrompt = await this.promptTemplate.render(context.kernel, context.arguments)

    // Get the AI service from the kernel
    // For now, we'll look for any chat completion service
    let aiService: any = null
    let executionSettings: PromptExecutionSettings | undefined

    // Try to find a service that matches our execution settings
    if (this.promptExecutionSettings.size > 0) {
      for (const [serviceId, settings] of this.promptExecutionSettings.entries()) {
        const service = context.kernel.getService(serviceId)
        if (service) {
          aiService = service
          executionSettings = settings
          break
        }
      }
    }

    // If no service found via settings, try to find any chat completion service by checking for the method
    if (!aiService) {
      for (const service of context.kernel.services.values()) {
        if (typeof (service as any).getChatMessageContents === 'function') {
          aiService = service
          // Use default execution settings if available
          executionSettings = this.promptExecutionSettings.get('default')
          break
        }
      }
    }

    if (!aiService) {
      throw new Error('No AI service found in kernel. Please add a chat completion service.')
    }

    // Check if it's a chat completion service by checking for the required method
    if (typeof aiService.getChatMessageContents === 'function') {
      // Create chat history from rendered prompt
      const chatHistory = ChatHistory.fromRenderedPrompt(renderedPrompt)

      try {
        const chatMessageContents = await aiService.getChatMessageContents(chatHistory, executionSettings || {}, {
          kernel: context.kernel,
          arguments: context.arguments,
        })

        if (!chatMessageContents || chatMessageContents.length === 0) {
          throw new Error(`No completions returned while invoking function ${this.name}`)
        }

        // Create function result
        context.result = new FunctionResult({
          function: this.metadata,
          value: chatMessageContents,
          metadata: {
            renderedPrompt,
          },
        })
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error)
        throw new Error(`Error occurred while invoking function ${this.name}: ${message}`, { cause: error })
      }
      return
    }

    // TODO: Add support for TextCompletionClientBase, TextToImageClientBase, etc.
    throw new Error(
      `Service type '${aiService.constructor.name}' is not supported yet. Currently only ChatCompletionClientBase is supported.`
    )
  }

  /**
   * Internal streaming invoke method implementation.
   * @param context - The function invocation context.
   */
  protected async _invokeInternalStream(context: FunctionInvocationContext): Promise<void> {
    const { FunctionResult } = await import('./function-result.js')
    const { ChatHistory } = await import('../contents/chat-history.js')

    // Render the prompt
    const renderedPrompt = await this.promptTemplate.render(context.kernel, context.arguments)

    // Get the AI service from the kernel
    let aiService: any = null
    let executionSettings: PromptExecutionSettings | undefined

    // Try to find a service that matches our execution settings
    if (this.promptExecutionSettings.size > 0) {
      for (const [serviceId, settings] of this.promptExecutionSettings.entries()) {
        const service = context.kernel.getService(serviceId)
        if (service) {
          aiService = service
          executionSettings = settings
          break
        }
      }
    }

    // If no service found via settings, try to find any chat completion service
    if (!aiService) {
      for (const service of context.kernel.services.values()) {
        if (typeof (service as any).getStreamingChatMessageContents === 'function') {
          aiService = service
          executionSettings = this.promptExecutionSettings.get('default')
          break
        }
      }
    }

    if (!aiService) {
      throw new Error('No AI service found in kernel. Please add a chat completion service.')
    }

    // Handle chat completion service streaming
    if (typeof aiService.getStreamingChatMessageContents === 'function') {
      const chatHistory = ChatHistory.fromRenderedPrompt(renderedPrompt)
      const value = aiService.getStreamingChatMessageContents(chatHistory, executionSettings || {}, {
        kernel: context.kernel,
        arguments: context.arguments,
      })

      context.result = new FunctionResult({
        function: this.metadata,
        value: value,
        renderedPrompt: renderedPrompt,
      })
      return
    }

    // Handle text completion service streaming
    if (typeof (aiService as any).getStreamingTextContents === 'function') {
      const value = aiService.getStreamingTextContents(renderedPrompt, executionSettings || {})

      context.result = new FunctionResult({
        function: this.metadata,
        value: value,
        renderedPrompt: renderedPrompt,
      })
      return
    }

    throw new Error(
      `Service type '${aiService.constructor.name}' is not a valid AI service for streaming. ` +
        'Only services with getStreamingChatMessageContents or getStreamingTextContents are supported.'
    )
  }
}
