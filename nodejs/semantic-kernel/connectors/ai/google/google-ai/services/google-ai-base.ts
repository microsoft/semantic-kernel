import { GoogleAISettings } from '../google-ai-settings'

/**
 * Google AI Service base class.
 */
export abstract class GoogleAIBase {
  static readonly MODEL_PROVIDER_NAME: string = 'googleai'

  serviceSettings: GoogleAISettings
  client: any | null = null // Replace 'any' with the actual GenAI client type

  constructor(serviceSettings: GoogleAISettings) {
    this.serviceSettings = serviceSettings
  }
}
