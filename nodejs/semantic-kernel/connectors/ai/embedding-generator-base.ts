import { AIServiceClientBase, PromptExecutionSettings } from '../../services/ai-service-client-base'

/**
 * Base class for embedding generators.
 *
 * @experimental This class is experimental and may change in future versions.
 */
export abstract class EmbeddingGeneratorBase extends AIServiceClientBase {
  /**
   * Returns embeddings for the given texts as a 2D array of numbers.
   *
   * @param texts - The texts to generate embeddings for
   * @param settings - The settings to use for the request, optional
   * @param kwargs - Additional arguments to pass to the request
   * @returns A promise that resolves to a 2D array of embeddings
   */
  abstract generateEmbeddings(
    texts: string[],
    settings?: PromptExecutionSettings,
    ...kwargs: any[]
  ): Promise<number[][]>

  /**
   * Returns embeddings for the given texts in the unedited format.
   *
   * This is not implemented for all embedding services, falling back to the generateEmbeddings method.
   *
   * @param texts - The texts to generate embeddings for
   * @param settings - The settings to use for the request, optional
   * @param kwargs - Additional arguments to pass to the request
   * @returns A promise that resolves to embeddings in their raw format
   */
  async generateRawEmbeddings(texts: string[], settings?: PromptExecutionSettings, ...kwargs: any[]): Promise<any> {
    return await this.generateEmbeddings(texts, settings, ...kwargs)
  }
}
