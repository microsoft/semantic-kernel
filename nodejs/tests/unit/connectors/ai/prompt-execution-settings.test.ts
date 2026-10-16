import { PromptExecutionSettings } from '../../../../semantic-kernel/connectors/ai/prompt-execution-settings'

describe('PromptExecutionSettings', () => {
  describe('constructor', () => {
    it('should initialize with default values', () => {
      const settings = new PromptExecutionSettings()
      expect(settings.serviceId).toBeUndefined()
      expect(settings.extensionData).toEqual({})
    })

    it('should initialize with provided data', () => {
      const extData = { test: 'test' }
      const settings = new PromptExecutionSettings({
        serviceId: 'test',
        extensionData: extData,
      })
      expect(settings.serviceId).toBe('test')
      expect(settings.extensionData.test).toBe('test')
    })
  })
})
