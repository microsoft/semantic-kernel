import { combineFilterDicts } from '../../../../semantic-kernel/connectors/ai/function-calling-utils'
import {
  FunctionChoiceBehavior,
  FunctionFilters,
  Kernel,
} from '../../../../semantic-kernel/connectors/ai/function-choice-behavior'
import { FunctionChoiceType } from '../../../../semantic-kernel/connectors/ai/function-choice-type'

const DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS = 5

// Mock Kernel
class MockKernel implements Kernel {
  getListOfFunctionMetadata(_filters: FunctionFilters): any[] {
    return []
  }

  getFullListOfFunctionMetadata(): any[] {
    return []
  }
}

describe('FunctionChoiceBehavior', () => {
  let kernel: Kernel
  let updateSettingsCallback: ReturnType<typeof jest.fn>

  beforeEach(() => {
    kernel = new MockKernel()
    updateSettingsCallback = jest.fn()
  })

  describe('Auto', () => {
    it('should create auto behavior with correct settings', () => {
      const behavior = FunctionChoiceBehavior.Auto(true)
      expect(behavior.type).toBe(FunctionChoiceType.AUTO)
      expect(behavior.maximumAutoInvokeAttempts).toBe(DEFAULT_MAX_AUTO_INVOKE_ATTEMPTS)
    })
  })

  describe('NoneInvoke', () => {
    it('should create none invoke behavior with correct settings', () => {
      const behavior = FunctionChoiceBehavior.NoneInvoke()
      expect(behavior.type).toBe(FunctionChoiceType.NONE)
      expect(behavior.maximumAutoInvokeAttempts).toBe(0)
    })
  })

  describe('Required', () => {
    it('should create required behavior with correct settings', () => {
      const expectedFilters: FunctionFilters = { includedFunctions: ['plugin1-func1'] }
      const behavior = FunctionChoiceBehavior.Required(true, expectedFilters)
      expect(behavior.type).toBe(FunctionChoiceType.REQUIRED)
      expect(behavior.maximumAutoInvokeAttempts).toBe(1)
      expect(behavior.filters).toEqual(expectedFilters)
    })
  })

  describe('fromDict', () => {
    it.each([
      ['auto', 5],
      ['none', 0],
      ['required', 1],
    ])('should create %s behavior from dict with maxAutoInvokeAttempts=%i', (type, maxAutoInvokeAttempts) => {
      const data = {
        type,
        filters: { includedFunctions: ['plugin1-func1', 'plugin2-func2'] },
        maximumAutoInvokeAttempts: maxAutoInvokeAttempts,
      }
      const behavior = FunctionChoiceBehavior.fromDict(data)
      expect(behavior.type).toBe(FunctionChoiceType[type.toUpperCase() as keyof typeof FunctionChoiceType])
      expect(behavior.filters).toEqual({ includedFunctions: ['plugin1-func1', 'plugin2-func2'] })
      expect(behavior.maximumAutoInvokeAttempts).toBe(maxAutoInvokeAttempts)
    })

    it.each([
      ['auto', 5],
      ['none', 0],
      ['required', 1],
    ])('should create %s behavior from dict with same filters and functions', (type, maxAutoInvokeAttempts) => {
      const data = {
        type,
        filters: { includedFunctions: ['plugin1-func1', 'plugin2-func2'] },
        functions: ['plugin1-func1', 'plugin2-func2'],
        maximumAutoInvokeAttempts: maxAutoInvokeAttempts,
      }
      const behavior = FunctionChoiceBehavior.fromDict(data)
      expect(behavior.type).toBe(FunctionChoiceType[type.toUpperCase() as keyof typeof FunctionChoiceType])
      expect(behavior.filters).toEqual({ includedFunctions: ['plugin1-func1', 'plugin2-func2'] })
      expect(behavior.maximumAutoInvokeAttempts).toBe(maxAutoInvokeAttempts)
    })

    it.each([
      ['auto', 5],
      ['none', 0],
      ['required', 1],
    ])('should create %s behavior from dict with different filters and functions', (type, maxAutoInvokeAttempts) => {
      const data = {
        type,
        filters: { includedFunctions: ['plugin1-func1', 'plugin2-func2'] },
        functions: ['plugin3-func3'],
        maximumAutoInvokeAttempts: maxAutoInvokeAttempts,
      }
      const behavior = FunctionChoiceBehavior.fromDict(data)
      expect(behavior.type).toBe(FunctionChoiceType[type.toUpperCase() as keyof typeof FunctionChoiceType])
      expect(behavior.filters).toEqual({
        includedFunctions: ['plugin1-func1', 'plugin2-func2', 'plugin3-func3'],
      })
      expect(behavior.maximumAutoInvokeAttempts).toBe(maxAutoInvokeAttempts)
    })
  })

  describe('properties', () => {
    let behavior: FunctionChoiceBehavior

    beforeEach(() => {
      behavior = new FunctionChoiceBehavior()
    })

    it('should get and set enableKernelFunctions', () => {
      behavior.enableKernelFunctions = false
      expect(behavior.enableKernelFunctions).toBe(false)
    })

    it('should get and set maximumAutoInvokeAttempts', () => {
      behavior.maximumAutoInvokeAttempts = 10
      expect(behavior.maximumAutoInvokeAttempts).toBe(10)
    })

    it('should get and set autoInvokeKernelFunctions', () => {
      expect(behavior.autoInvokeKernelFunctions).toBe(true)
      behavior.autoInvokeKernelFunctions = false
      expect(behavior.autoInvokeKernelFunctions).toBe(false)
      expect(behavior.maximumAutoInvokeAttempts).toBe(0)
      behavior.autoInvokeKernelFunctions = true
      expect(behavior.autoInvokeKernelFunctions).toBe(true)
      expect(behavior.maximumAutoInvokeAttempts).toBe(5)
    })
  })

  describe('auto invoke kernel functions', () => {
    it('should enable auto invoke with correct settings', () => {
      const fcb = FunctionChoiceBehavior.Auto(true)
      expect(fcb).toBeDefined()
      expect(fcb.enableKernelFunctions).toBe(true)
      expect(fcb.maximumAutoInvokeAttempts).toBe(5)
      expect(fcb.autoInvokeKernelFunctions).toBe(true)
    })
  })

  describe('none invoke kernel functions', () => {
    it('should create none invoke with correct settings', () => {
      const fcb = FunctionChoiceBehavior.NoneInvoke()
      expect(fcb).toBeDefined()
      expect(fcb.enableKernelFunctions).toBe(true)
      expect(fcb.maximumAutoInvokeAttempts).toBe(0)
      expect(fcb.autoInvokeKernelFunctions).toBe(false)
    })
  })

  describe('enable functions', () => {
    it('should enable functions with filters', () => {
      const fcb = FunctionChoiceBehavior.Auto(true, { excludedPlugins: ['test'] })
      expect(fcb).toBeDefined()
      expect(fcb.enableKernelFunctions).toBe(true)
      expect(fcb.maximumAutoInvokeAttempts).toBe(5)
      expect(fcb.autoInvokeKernelFunctions).toBe(true)
      expect(fcb.filters).toEqual({ excludedPlugins: ['test'] })
    })
  })

  describe('required function', () => {
    it('should create required with correct settings', () => {
      const fcb = FunctionChoiceBehavior.Required(true, { includedFunctions: ['test'] })
      expect(fcb).toBeDefined()
      expect(fcb.enableKernelFunctions).toBe(true)
      expect(fcb.maximumAutoInvokeAttempts).toBe(1)
      expect(fcb.autoInvokeKernelFunctions).toBe(true)
    })
  })

  describe('configure auto invoke kernel functions', () => {
    it('should call update settings callback', () => {
      const fcb = FunctionChoiceBehavior.Auto(true)
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).toHaveBeenCalled()
    })

    it('should skip when enableKernelFunctions is false', () => {
      const fcb = FunctionChoiceBehavior.Auto(true)
      fcb.enableKernelFunctions = false
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).not.toHaveBeenCalled()
    })
  })

  describe('configure none invoke kernel functions', () => {
    it('should call update settings callback', () => {
      const fcb = FunctionChoiceBehavior.NoneInvoke()
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).toHaveBeenCalled()
    })

    it('should skip when enableKernelFunctions is false', () => {
      const fcb = FunctionChoiceBehavior.NoneInvoke()
      fcb.enableKernelFunctions = false
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).not.toHaveBeenCalled()
    })
  })

  describe('configure enable functions', () => {
    it('should call update settings callback', () => {
      const fcb = FunctionChoiceBehavior.Auto(true, { excludedPlugins: ['test'] })
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).toHaveBeenCalled()
    })

    it('should skip when enableKernelFunctions is false', () => {
      const fcb = FunctionChoiceBehavior.Auto(true, { excludedPlugins: ['test'] })
      fcb.enableKernelFunctions = false
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).not.toHaveBeenCalled()
    })
  })

  describe('configure required function', () => {
    it('should call update settings callback', () => {
      const fcb = FunctionChoiceBehavior.Required(true, { includedFunctions: ['plugin1-func1'] })
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).toHaveBeenCalled()
    })

    it('should preserve maximumAutoInvokeAttempts when updated', () => {
      const fcb = FunctionChoiceBehavior.Required(true, { includedFunctions: ['plugin1-func1'] })
      fcb.maximumAutoInvokeAttempts = 10
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).toHaveBeenCalled()
      expect(fcb.maximumAutoInvokeAttempts).toBe(10)
    })

    it('should skip when enableKernelFunctions is false', () => {
      const fcb = FunctionChoiceBehavior.Required(true, { includedFunctions: ['test'] })
      fcb.enableKernelFunctions = false
      fcb.configure(kernel, updateSettingsCallback, {})
      expect(updateSettingsCallback).not.toHaveBeenCalled()
    })
  })

  describe('combineFilterDicts', () => {
    it('should throw error when filter values are not arrays', () => {
      const dict1 = { filter1: ['a', 'b', 'c'] }
      const dict2 = { filter1: 'not_a_list' as any } // This should trigger the error

      expect(() => combineFilterDicts(dict1, dict2)).toThrow("Values for filter key 'filter1' are not lists.")
    })
  })

  describe('fromString', () => {
    it('should create auto from string', () => {
      const auto = FunctionChoiceBehavior.fromString('auto')
      expect(auto.type).toBe(FunctionChoiceBehavior.Auto().type)
      expect(auto.maximumAutoInvokeAttempts).toBe(FunctionChoiceBehavior.Auto().maximumAutoInvokeAttempts)
    })

    it('should create none from string', () => {
      const none = FunctionChoiceBehavior.fromString('none')
      expect(none.type).toBe(FunctionChoiceBehavior.NoneInvoke().type)
      expect(none.maximumAutoInvokeAttempts).toBe(FunctionChoiceBehavior.NoneInvoke().maximumAutoInvokeAttempts)
    })

    it('should create required from string', () => {
      const required = FunctionChoiceBehavior.fromString('required')
      expect(required.type).toBe(FunctionChoiceBehavior.Required().type)
      expect(required.maximumAutoInvokeAttempts).toBe(FunctionChoiceBehavior.Required().maximumAutoInvokeAttempts)
    })

    it('should throw error for invalid string', () => {
      expect(() => FunctionChoiceBehavior.fromString('invalid')).toThrow(
        'The specified type `invalid` is not supported. Allowed types are: `auto`, `none`, `required`.'
      )
    })
  })
})
