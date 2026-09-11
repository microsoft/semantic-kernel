import { TokenCredential } from '@azure/identity'
import { AzureOpenAI } from 'openai'
import { getEntraAuthToken } from '../../../../utils/authentication/entra-id-authentication'
import { APP_INFO, prependSemanticKernelToUserAgent } from '../../../../utils/telemetry/user-agent'
import { OpenAIHandler } from './open-ai-handler'
import { OpenAIModelTypes } from './open-ai-model-types'

const DEFAULT_AZURE_API_VERSION = '2024-10-21'
const USER_AGENT = 'User-Agent'

/**
 * Options for configuring Azure OpenAI connection.
 */
export interface AzureOpenAIConfigOptions {
  deploymentName: string
  aiModelType: OpenAIModelTypes
  endpoint?: string
  baseUrl?: string
  apiVersion?: string
  serviceId?: string
  apiKey?: string
  adToken?: string
  adTokenProvider?: () => string | Promise<string>
  tokenEndpoint?: string
  defaultHeaders?: Record<string, string>
  client?: AzureOpenAI
  instructionRole?: string
  credential?: TokenCredential
  [key: string]: any
}

/**
 * Internal class for configuring a connection to an Azure OpenAI service.
 */
export class AzureOpenAIConfigBase extends OpenAIHandler {
  deploymentName: string
  serviceId?: string
  instructionRole?: string

  constructor(options: AzureOpenAIConfigOptions) {
    const {
      deploymentName,
      aiModelType,
      endpoint,
      baseUrl,
      apiVersion = DEFAULT_AZURE_API_VERSION,
      serviceId,
      apiKey,
      adToken,
      adTokenProvider,
      tokenEndpoint,
      defaultHeaders,
      client,
      instructionRole,
      credential,
      ...kwargs
    } = options

    // Merge APP_INFO into the headers if it exists
    let mergedHeaders: Record<string, string> = defaultHeaders ? { ...defaultHeaders } : {}
    if (APP_INFO) {
      mergedHeaders = { ...mergedHeaders, ...APP_INFO }
      mergedHeaders = prependSemanticKernelToUserAgent(mergedHeaders)
    }

    let finalClient = client

    if (!finalClient) {
      // If the client is None, the api_key is none, the ad_token is none, and the ad_token_provider is none,
      // then we will attempt to get the ad_token using the default endpoint specified in the Azure OpenAI
      // settings.
      let finalAdToken = adToken
      if (!apiKey && !adTokenProvider && !adToken && tokenEndpoint && credential) {
        // Note: This is async in Python, but we need to handle it synchronously in constructor
        // In real implementation, you might want to pass this as a promise or handle differently
        getEntraAuthToken(credential, tokenEndpoint).then((token) => {
          finalAdToken = token || undefined
        })
      }

      if (!apiKey && !finalAdToken && !adTokenProvider && !credential) {
        throw new Error('Please provide either apiKey, adToken, adTokenProvider, credential or a client.')
      }

      if (!endpoint && !baseUrl) {
        throw new Error('Please provide an endpoint or a baseUrl')
      }

      const args: any = {
        defaultHeaders: mergedHeaders,
      }

      if (apiVersion) {
        args.apiVersion = apiVersion
      }
      if (finalAdToken) {
        args.azureADToken = finalAdToken
      }
      if (adTokenProvider) {
        args.azureADTokenProvider = adTokenProvider
      }
      if (apiKey) {
        args.apiKey = apiKey
      }
      if (baseUrl) {
        args.baseURL = baseUrl
      }
      if (endpoint && !baseUrl) {
        args.endpoint = endpoint
      }
      // TODO: Remove the check on model type when the package fixes the issue
      if (deploymentName && aiModelType !== OpenAIModelTypes.REALTIME) {
        args.deployment = deploymentName
      }

      if (kwargs.websocketBaseUrl) {
        args.websocketBaseUrl = kwargs.websocketBaseUrl
      }

      finalClient = new AzureOpenAI(args)
    }

    super(finalClient, aiModelType)

    this.deploymentName = deploymentName
    this.serviceId = serviceId
    this.instructionRole = instructionRole
  }

  /**
   * Convert the configuration to a dictionary.
   *
   * @returns A dictionary representation of the configuration
   */
  toDict(): Record<string, any> {
    const client = this.client as any

    const clientSettings: Record<string, any> = {
      baseUrl: client.baseURL || '',
      apiVersion: client._options?.defaultQuery?.['api-version'] || DEFAULT_AZURE_API_VERSION,
      apiKey: client.apiKey,
      adToken: client._azureADToken,
      adTokenProvider: client._azureADTokenProvider,
      defaultHeaders: Object.fromEntries(Object.entries(client.defaultHeaders || {}).filter(([k]) => k !== USER_AGENT)),
    }

    const base: Record<string, any> = {
      deploymentName: this.deploymentName,
      aiModelType: this.aiModelType,
    }

    if (this.serviceId) {
      base.serviceId = this.serviceId
    }
    if (this.instructionRole) {
      base.instructionRole = this.instructionRole
    }

    return {
      ...base,
      ...clientSettings,
    }
  }
}
