import { GoogleAISettings } from '../../../../../../semantic-kernel/connectors/ai/google/google-ai/google-ai-settings'

describe('GoogleAISettings', () => {
  // Save original environment variables
  const originalEnv = process.env

  beforeEach(() => {
    // Reset environment before each test
    jest.resetModules()
    process.env = { ...originalEnv }
  })

  afterAll(() => {
    // Restore original environment
    process.env = originalEnv
  })

  describe('constructor', () => {
    it('should create instance with default values', () => {
      const settings = new GoogleAISettings()

      expect(settings.geminiModelId).toBeUndefined()
      expect(settings.embeddingModelId).toBeUndefined()
      expect(settings.apiKey).toBeUndefined()
      expect(settings.cloudProjectId).toBeUndefined()
      expect(settings.cloudRegion).toBeUndefined()
      expect(settings.useVertexAI).toBe(false)
    })

    it('should create instance with custom values', () => {
      const settings = new GoogleAISettings({
        geminiModelId: 'gemini-1.5-pro',
        embeddingModelId: 'text-embedding-004',
        apiKey: 'test-api-key',
        cloudProjectId: 'test-project-id',
        cloudRegion: 'us-central1',
        useVertexAI: true,
      })

      expect(settings.geminiModelId).toBe('gemini-1.5-pro')
      expect(settings.embeddingModelId).toBe('text-embedding-004')
      expect(settings.apiKey).toBe('test-api-key')
      expect(settings.cloudProjectId).toBe('test-project-id')
      expect(settings.cloudRegion).toBe('us-central1')
      expect(settings.useVertexAI).toBe(true)
    })

    it('should create instance with partial config', () => {
      const settings = new GoogleAISettings({
        geminiModelId: 'gemini-1.5-pro',
        apiKey: 'test-api-key',
      })

      expect(settings.geminiModelId).toBe('gemini-1.5-pro')
      expect(settings.apiKey).toBe('test-api-key')
      expect(settings.embeddingModelId).toBeUndefined()
      expect(settings.cloudProjectId).toBeUndefined()
      expect(settings.cloudRegion).toBeUndefined()
      expect(settings.useVertexAI).toBe(false)
    })

    it('should default useVertexAI to false when not provided', () => {
      const settings = new GoogleAISettings({
        apiKey: 'test-api-key',
      })

      expect(settings.useVertexAI).toBe(false)
    })
  })

  describe('fromEnvironment', () => {
    it('should load settings from environment variables', () => {
      process.env.GOOGLE_AI_GEMINI_MODEL_ID = 'gemini-1.5-pro'
      process.env.GOOGLE_AI_EMBEDDING_MODEL_ID = 'text-embedding-004'
      process.env.GOOGLE_AI_API_KEY = 'env-api-key'
      process.env.GOOGLE_AI_CLOUD_PROJECT_ID = 'env-project-id'
      process.env.GOOGLE_AI_CLOUD_REGION = 'us-west1'
      process.env.GOOGLE_AI_USE_VERTEXAI = 'true'

      const settings = GoogleAISettings.fromEnvironment()

      expect(settings.geminiModelId).toBe('gemini-1.5-pro')
      expect(settings.embeddingModelId).toBe('text-embedding-004')
      expect(settings.apiKey).toBe('env-api-key')
      expect(settings.cloudProjectId).toBe('env-project-id')
      expect(settings.cloudRegion).toBe('us-west1')
      expect(settings.useVertexAI).toBe(true)
    })

    it('should handle missing environment variables', () => {
      const settings = GoogleAISettings.fromEnvironment()

      expect(settings.geminiModelId).toBeUndefined()
      expect(settings.embeddingModelId).toBeUndefined()
      expect(settings.apiKey).toBeUndefined()
      expect(settings.cloudProjectId).toBeUndefined()
      expect(settings.cloudRegion).toBeUndefined()
      expect(settings.useVertexAI).toBe(false)
    })

    it('should parse useVertexAI as false when not "true"', () => {
      process.env.GOOGLE_AI_USE_VERTEXAI = 'false'

      const settings = GoogleAISettings.fromEnvironment()

      expect(settings.useVertexAI).toBe(false)
    })

    it('should parse useVertexAI as false when set to arbitrary string', () => {
      process.env.GOOGLE_AI_USE_VERTEXAI = 'yes'

      const settings = GoogleAISettings.fromEnvironment()

      expect(settings.useVertexAI).toBe(false)
    })

    it('should parse useVertexAI as true only when exactly "true"', () => {
      process.env.GOOGLE_AI_USE_VERTEXAI = 'true'

      const settings = GoogleAISettings.fromEnvironment()

      expect(settings.useVertexAI).toBe(true)
    })
  })

  describe('validate', () => {
    describe('when useVertexAI is false', () => {
      it('should not throw when apiKey is provided', () => {
        const settings = new GoogleAISettings({
          apiKey: 'test-api-key',
          useVertexAI: false,
        })

        expect(() => settings.validate()).not.toThrow()
      })

      it('should throw when apiKey is missing', () => {
        const settings = new GoogleAISettings({
          useVertexAI: false,
        })

        expect(() => settings.validate()).toThrow('GoogleAI settings validation failed')
        expect(() => settings.validate()).toThrow('api_key is required when use_vertexai is false')
      })

      it('should not require cloudProjectId and cloudRegion', () => {
        const settings = new GoogleAISettings({
          apiKey: 'test-api-key',
          useVertexAI: false,
        })

        expect(() => settings.validate()).not.toThrow()
      })
    })

    describe('when useVertexAI is true', () => {
      it('should not throw when cloudProjectId and cloudRegion are provided', () => {
        const settings = new GoogleAISettings({
          cloudProjectId: 'test-project',
          cloudRegion: 'us-central1',
          useVertexAI: true,
        })

        expect(() => settings.validate()).not.toThrow()
      })

      it('should throw when cloudProjectId is missing', () => {
        const settings = new GoogleAISettings({
          cloudRegion: 'us-central1',
          useVertexAI: true,
        })

        expect(() => settings.validate()).toThrow('GoogleAI settings validation failed')
        expect(() => settings.validate()).toThrow('cloud_project_id is required when use_vertexai is true')
      })

      it('should throw when cloudRegion is missing', () => {
        const settings = new GoogleAISettings({
          cloudProjectId: 'test-project',
          useVertexAI: true,
        })

        expect(() => settings.validate()).toThrow('GoogleAI settings validation failed')
        expect(() => settings.validate()).toThrow('cloud_region is required when use_vertexai is true')
      })

      it('should throw with multiple errors when both cloudProjectId and cloudRegion are missing', () => {
        const settings = new GoogleAISettings({
          useVertexAI: true,
        })

        expect(() => settings.validate()).toThrow('GoogleAI settings validation failed')
        expect(() => settings.validate()).toThrow('cloud_project_id is required when use_vertexai is true')
        expect(() => settings.validate()).toThrow('cloud_region is required when use_vertexai is true')
      })

      it('should not require apiKey when using VertexAI', () => {
        const settings = new GoogleAISettings({
          cloudProjectId: 'test-project',
          cloudRegion: 'us-central1',
          useVertexAI: true,
        })

        expect(() => settings.validate()).not.toThrow()
      })
    })
  })

  describe('ENV_PREFIX', () => {
    it('should have correct environment prefix', () => {
      expect(GoogleAISettings.ENV_PREFIX).toBe('GOOGLE_AI_')
    })
  })
})
