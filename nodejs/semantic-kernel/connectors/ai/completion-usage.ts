import type { CompletionUsage as OpenAICompletionUsage } from 'openai/resources/completions'

/**
 * Details about prompt tokens usage.
 */
export interface PromptTokensDetails {
  /** Number of cached tokens in the prompt */
  cachedTokens?: number
  /** Number of audio tokens in the prompt */
  audioTokens?: number
  [key: string]: any
}

/**
 * Details about completion tokens usage.
 */
export interface CompletionTokensDetails {
  /** Number of reasoning tokens generated */
  reasoningTokens?: number
  /** Number of audio tokens generated */
  audioTokens?: number
  /** Number of tokens accepted from predictions */
  acceptedPredictionTokens?: number
  /** Number of tokens rejected from predictions */
  rejectedPredictionTokens?: number
  [key: string]: any
}

/**
 * A class representing the usage of tokens in a completion request.
 */
export class CompletionUsage {
  /** Number of tokens in the prompt */
  promptTokens?: number

  /** Detailed breakdown of prompt tokens */
  promptTokensDetails?: PromptTokensDetails

  /** Number of tokens in the completion */
  completionTokens?: number

  /** Detailed breakdown of completion tokens */
  completionTokensDetails?: CompletionTokensDetails

  constructor(options?: {
    promptTokens?: number
    promptTokensDetails?: PromptTokensDetails
    completionTokens?: number
    completionTokensDetails?: CompletionTokensDetails
  }) {
    this.promptTokens = options?.promptTokens
    this.promptTokensDetails = options?.promptTokensDetails
    this.completionTokens = options?.completionTokens
    this.completionTokensDetails = options?.completionTokensDetails
  }

  /**
   * Create a CompletionUsage instance from an OpenAI CompletionUsage instance.
   *
   * @param openaiCompletionUsage - The OpenAI completion usage object
   * @returns A new CompletionUsage instance
   */
  static fromOpenAI(openaiCompletionUsage: OpenAICompletionUsage): CompletionUsage {
    return new CompletionUsage({
      promptTokens: openaiCompletionUsage.prompt_tokens,
      promptTokensDetails: openaiCompletionUsage.prompt_tokens_details
        ? {
            cachedTokens: (openaiCompletionUsage.prompt_tokens_details as any).cached_tokens,
            audioTokens: (openaiCompletionUsage.prompt_tokens_details as any).audio_tokens,
            ...openaiCompletionUsage.prompt_tokens_details,
          }
        : undefined,
      completionTokens: openaiCompletionUsage.completion_tokens,
      completionTokensDetails: openaiCompletionUsage.completion_tokens_details
        ? {
            reasoningTokens: (openaiCompletionUsage.completion_tokens_details as any).reasoning_tokens,
            audioTokens: (openaiCompletionUsage.completion_tokens_details as any).audio_tokens,
            acceptedPredictionTokens: (openaiCompletionUsage.completion_tokens_details as any)
              .accepted_prediction_tokens,
            rejectedPredictionTokens: (openaiCompletionUsage.completion_tokens_details as any)
              .rejected_prediction_tokens,
            ...openaiCompletionUsage.completion_tokens_details,
          }
        : undefined,
    })
  }

  /**
   * Combine two CompletionUsage instances by summing their token counts.
   *
   * @param other - The other CompletionUsage instance to combine with
   * @returns A new CompletionUsage instance with combined token counts
   */
  add(other: CompletionUsage): CompletionUsage {
    /**
     * Merge two details objects by summing their fields.
     */
    function mergeDetails<T extends Record<string, any>>(a?: T, b?: T): T | undefined {
      if (!a && !b) {
        return undefined
      }

      const result: Record<string, any> = {}
      const allKeys = new Set([...Object.keys(a || {}), ...Object.keys(b || {})])

      for (const key of allKeys) {
        const x = a?.[key]
        const y = b?.[key]

        if (typeof x === 'number' || typeof y === 'number') {
          result[key] = (x || 0) + (y || 0)
        } else if (x !== undefined) {
          result[key] = x
        } else if (y !== undefined) {
          result[key] = y
        }
      }

      return result as T
    }

    return new CompletionUsage({
      promptTokens: (this.promptTokens || 0) + (other.promptTokens || 0),
      completionTokens: (this.completionTokens || 0) + (other.completionTokens || 0),
      promptTokensDetails: mergeDetails(this.promptTokensDetails, other.promptTokensDetails),
      completionTokensDetails: mergeDetails(this.completionTokensDetails, other.completionTokensDetails),
    })
  }

  /**
   * Get the total number of tokens (prompt + completion).
   */
  get totalTokens(): number {
    return (this.promptTokens || 0) + (this.completionTokens || 0)
  }
}
