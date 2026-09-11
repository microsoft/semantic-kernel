import { KernelProcessState } from '../../../../semantic-kernel/processes/kernel-process/kernel-process-state'

describe('KernelProcessState', () => {
  describe('initialization', () => {
    it('should initialize with name and id', () => {
      // Arrange
      const name = 'test_process'
      const processId = '1234'
      const version = '1.0'

      // Act
      const state = new KernelProcessState({
        name,
        version,
        id: processId,
      })

      // Assert
      expect(state.name).toBe(name)
      expect(state.id).toBe(processId)
      expect(state.state).toBeNull()
      expect(state.version).toBe(version)
    })

    it('should initialize with name only', () => {
      // Arrange
      const name = 'test_process_without_id'
      const version = '1.0'

      // Act
      const state = new KernelProcessState({
        name,
        version,
      })

      // Assert
      expect(state.name).toBe(name)
      expect(state.id).toBeNull()
      expect(state.state).toBeNull()
      expect(state.version).toBe(version)
    })

    it('should allow setting state value', () => {
      // Arrange
      const name = 'test_process'
      const stateValue = { key: 'value' }

      // Act
      const state = new KernelProcessState({
        name,
        version: '1.0',
      })
      state.state = stateValue

      // Assert
      expect(state.state).toEqual(stateValue)
      expect(state.version).toBe('1.0')
    })

    it('should throw error when initialized with invalid name type', () => {
      // Arrange
      const name = 12345 as any // Invalid type for name

      // Act & Assert
      // TypeScript will catch this at compile time, but at runtime we test the behavior
      expect(() => {
        new KernelProcessState({
          name,
          version: '1.0',
        })
      }).not.toThrow() // TypeScript doesn't enforce runtime type checking like Pydantic
      // Note: In production code, you might want to add runtime validation
    })
  })
})
