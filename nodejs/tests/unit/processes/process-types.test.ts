import { getGenericStateType } from '../../../semantic-kernel/processes/process-types'

// Test classes for various scenarios
class ConcreteState {}

class ConcreteKernelProcessStep {
  static __stateType__ = ConcreteState
  state!: ConcreteState
}

class OptionalStateKernelProcessStep {
  static __stateType__ = ConcreteState
  state!: ConcreteState | null
}

class OptionalStateKernelProcessStepOldSyntax {
  static __stateType__ = ConcreteState
  state!: ConcreteState | null
}

class TypeVarStateKernelProcessStep<TState = any> {
  state!: TState
}

class NoStateKernelProcessStep {}

class InheritedKernelProcessStep extends ConcreteKernelProcessStep {}

describe('getGenericStateType', () => {
  it('should get generic state type for concrete state', () => {
    const result = getGenericStateType(ConcreteKernelProcessStep)
    expect(result).toBe(ConcreteState)
  })

  it('should get generic state type for optional state', () => {
    const result = getGenericStateType(OptionalStateKernelProcessStep)
    expect(result).toBe(ConcreteState)
  })

  it('should get generic state type for optional state with old syntax', () => {
    const result = getGenericStateType(OptionalStateKernelProcessStepOldSyntax)
    expect(result).toBe(ConcreteState)
  })

  it('should return null for typevar state', () => {
    const result = getGenericStateType(TypeVarStateKernelProcessStep)
    expect(result).toBeNull()
  })

  it('should return null for no state', () => {
    const result = getGenericStateType(NoStateKernelProcessStep)
    expect(result).toBeNull()
  })

  it('should get generic state type for inherited step', () => {
    const result = getGenericStateType(InheritedKernelProcessStep)
    expect(result).toBe(ConcreteState)
  })

  it('should return null when exception occurs', () => {
    // Create a mock class that throws an error when accessing __stateType__
    const ThrowingClass = class {
      static get __stateType__() {
        throw new Error('Mocked exception')
      }
    }

    const result = getGenericStateType(ThrowingClass)
    expect(result).toBeNull()
  })
})
