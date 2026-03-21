import { KernelProcess } from '../../../../semantic-kernel/processes/kernel-process/kernel-process'
import { KernelProcessEdge } from '../../../../semantic-kernel/processes/kernel-process/kernel-process-edge'
import { KernelProcessState } from '../../../../semantic-kernel/processes/kernel-process/kernel-process-state'
import { KernelProcessStepInfo } from '../../../../semantic-kernel/processes/kernel-process/kernel-process-step-info'

describe('KernelProcess', () => {
  describe('initialization', () => {
    it('should initialize with valid parameters', () => {
      // Arrange
      const state = new KernelProcessState({
        name: 'valid_state',
        version: '1.0.0',
      })
      const steps = [
        new KernelProcessStepInfo({
          innerStepType: class MockStep {},
          state: new KernelProcessState({ name: 'step1', version: '1.0.0' }),
          outputEdges: {},
        }),
      ]
      const edges: Record<string, KernelProcessEdge[]> = {
        step1: [
          new KernelProcessEdge({
            sourceStepId: 'step1',
            outputTarget: { stepId: 'step2', functionName: 'process' },
          }),
        ],
      }

      // Act
      const process = new KernelProcess({
        state,
        steps,
        edges,
      })

      // Assert
      expect(process.state).toBe(state)
      expect(process.steps).toEqual(steps)
      expect(process.outputEdges).toEqual(edges)
    })

    it('should throw error when initialized with no steps', () => {
      // Arrange
      const state = new KernelProcessState({
        name: 'state_without_steps',
        version: '1.0.0',
      })

      // Act & Assert
      expect(() => {
        new KernelProcess({
          state,
          steps: [] as any,
        })
      }).toThrow('steps cannot be null')
    })

    it('should throw error when initialized with no state', () => {
      // Arrange
      const steps = [
        new KernelProcessStepInfo({
          innerStepType: class MockStep {},
          state: new KernelProcessState({ name: 'step1', version: '1.0.0' }),
          outputEdges: {},
        }),
      ]
      const edges: Record<string, KernelProcessEdge[]> = {
        step1: [
          new KernelProcessEdge({
            sourceStepId: 'step1',
            outputTarget: { stepId: 'step2', functionName: 'process' },
          }),
        ],
      }

      // Act & Assert
      expect(() => {
        new KernelProcess({
          state: null as any,
          steps,
          edges,
        })
      }).toThrow('state cannot be null')
    })

    it('should throw error when initialized with no state name', () => {
      // Arrange
      const state = new KernelProcessState({
        name: null as any, // Invalid state name
        version: '1.0.0',
      })
      const steps = [
        new KernelProcessStepInfo({
          innerStepType: class MockStep {},
          state: new KernelProcessState({ name: 'step1', version: '1.0.0' }),
          outputEdges: {},
        }),
      ]

      // Act & Assert
      expect(() => {
        new KernelProcess({
          state,
          steps,
        })
      }).toThrow('state.name cannot be null')
    })
  })
})
