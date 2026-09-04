import { PromptExecutionSettings } from '../../prompt-execution-settings'

export type GoogleAIPromptExecutionSettingsParams = {
  stopSequences?: string[] | null
  responseMimeType?: 'text/plain' | 'application/json' | null
  responseSchema?: any | null
  candidateCount?: number | null
  maxOutputTokens?: number | null
  temperature?: number | null
  topP?: number | null
  topK?: number | null
}

export class GoogleAIPromptExecutionSettings extends PromptExecutionSettings {
  stopSequences?: string[] | null
  responseMimeType?: 'text/plain' | 'application/json' | null
  responseSchema?: any | null
  candidateCount?: number | null
  maxOutputTokens?: number | null
  temperature?: number | null
  topP?: number | null
  topK?: number | null

  constructor(params: GoogleAIPromptExecutionSettingsParams = {}) {
    super()
    this.stopSequences = params.stopSequences ?? null
    this.responseMimeType = params.responseMimeType ?? null
    this.responseSchema = params.responseSchema ?? null
    this.candidateCount = params.candidateCount ?? null
    this.maxOutputTokens = params.maxOutputTokens ?? null
    this.temperature = params.temperature ?? null
    this.topP = params.topP ?? null
    this.topK = params.topK ?? null
  }
}

export class GoogleAITextPromptExecutionSettings extends GoogleAIPromptExecutionSettings {
  // No additional fields
}

export type GoogleAIChatPromptExecutionSettingsParams = GoogleAIPromptExecutionSettingsParams & {
  tools?: Array<Record<string, any>> | null
  toolConfig?: Record<string, any> | null
}

export class GoogleAIChatPromptExecutionSettings extends GoogleAIPromptExecutionSettings {
  tools?: Array<Record<string, any>> | null
  toolConfig?: Record<string, any> | null

  constructor(params: GoogleAIChatPromptExecutionSettingsParams = {}) {
    super(params)
    this.tools = params.tools ?? null
    this.toolConfig = params.toolConfig ?? null
  }
}

export type GoogleAIEmbeddingPromptExecutionSettingsParams = {
  outputDimensionality?: number | null
}

export class GoogleAIEmbeddingPromptExecutionSettings extends PromptExecutionSettings {
  outputDimensionality?: number | null

  constructor(params: GoogleAIEmbeddingPromptExecutionSettingsParams = {}) {
    super()
    this.outputDimensionality = params.outputDimensionality ?? null
  }
}
