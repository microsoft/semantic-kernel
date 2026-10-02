import { StreamingTextContent } from '../../contents/streaming-text-content'
import { TextContent } from '../../contents/text-content'
import { AIServiceClientBase } from '../../services/ai-service-client-base'
import { PromptExecutionSettings } from './prompt-execution-settings'

/**
 * Base class for text completion AI services.
 * This abstract class defines the interface that all text completion services must implement.
 */
export abstract class TextCompletionClientBase extends AIServiceClientBase {
  // #region Internal methods to be implemented by the derived classes

  /**
   * Send a text completion request to the AI service.
   * This method must be implemented by derived classes.
   *
   * @param prompt - The prompt to send to the LLM
   * @param settings - Settings for the request
   * @returns A list of TextContent representing the response(s) from the LLM
   * @protected
   * @abstract
   */
  protected async _innerGetTextContents(_prompt: string, _settings: PromptExecutionSettings): Promise<TextContent[]> {
    throw new Error('The _innerGetTextContents method is not implemented.')
  }

  /**
   * Send a streaming text request to the AI service.
   * This method must be implemented by derived classes.
   *
   * @param prompt - The prompt to send to the LLM
   * @param settings - Settings for the request
   * @yields A stream of lists of StreamingTextContent representing the response(s) from the LLM
   * @protected
   * @abstract
   */
  // eslint-disable-next-line require-yield
  protected async *_innerGetStreamingTextContents(
    _prompt: string,
    _settings: PromptExecutionSettings
  ): AsyncGenerator<StreamingTextContent[], void, unknown> {
    throw new Error('The _innerGetStreamingTextContents method is not implemented.')
  }

  // #endregion

  // #region Public methods

  /**
   * Create text contents, in the number specified by the settings.
   *
   * @param prompt - The prompt to send to the LLM
   * @param settings - Settings for the request
   * @returns A list of TextContent representing the response(s) from the LLM
   */
  async getTextContents(prompt: string, settings: PromptExecutionSettings): Promise<TextContent[]> {
    // Create a deep copy of the settings to avoid modifying the original settings
    const settingsCopy = this._deepCopySettings(settings)

    return await this._innerGetTextContents(prompt, settingsCopy)
  }

  /**
   * This is the method that is called from the kernel to get a response from a text-optimized LLM.
   * Returns the first text content from the response.
   *
   * @param prompt - The prompt to send to the LLM
   * @param settings - Settings for the request
   * @returns A single TextContent representing the response from the LLM, or null if no response
   */
  async getTextContent(prompt: string, settings: PromptExecutionSettings): Promise<TextContent | null> {
    const result = await this.getTextContents(prompt, settings)

    if (result && result.length > 0) {
      return result[0]
    }

    // This should not happen, should error out before returning an empty list
    return null // pragma: no cover
  }

  /**
   * Create streaming text contents, in the number specified by the settings.
   *
   * @param prompt - The prompt to send to the LLM
   * @param settings - Settings for the request
   * @yields Lists of StreamingTextContent representing the streaming response(s) from the LLM
   */
  async *getStreamingTextContents(
    prompt: string,
    settings: PromptExecutionSettings
  ): AsyncGenerator<StreamingTextContent[], void, unknown> {
    // Create a deep copy of the settings to avoid modifying the original settings
    const settingsCopy = this._deepCopySettings(settings)

    for await (const contents of this._innerGetStreamingTextContents(prompt, settingsCopy)) {
      yield contents
    }
  }

  /**
   * This is the method that is called from the kernel to get a stream response from a text-optimized LLM.
   * Yields the first streaming text content from each chunk.
   *
   * @param prompt - The prompt to send to the LLM
   * @param settings - Settings for the request
   * @yields StreamingTextContent representing the streaming response from the LLM, or null if no content
   */
  async *getStreamingTextContent(
    prompt: string,
    settings: PromptExecutionSettings
  ): AsyncGenerator<StreamingTextContent | null, void, unknown> {
    for await (const contents of this.getStreamingTextContents(prompt, settings)) {
      if (contents && contents.length > 0) {
        yield contents[0]
      } else {
        // This should not happen, should error out before returning an empty list
        yield null // pragma: no cover
      }
    }
  }

  // #endregion

  // #region Helper methods

  /**
   * Create a deep copy of the settings object.
   * This prevents modifications to the original settings during processing.
   *
   * @param settings - The settings to copy
   * @returns A deep copy of the settings
   * @private
   */
  private _deepCopySettings(settings: PromptExecutionSettings): PromptExecutionSettings {
    // Use structured clone if available (Node 17+), otherwise use JSON serialization
    if (typeof structuredClone !== 'undefined') {
      return structuredClone(settings)
    }

    // Fallback to JSON-based deep copy
    // Note: This may not work for all object types (functions, symbols, etc.)
    return JSON.parse(JSON.stringify(settings))
  }

  // #endregion
}
