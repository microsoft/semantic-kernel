import type { KernelProcess } from './kernel-process/kernel-process'
import type { KernelProcessStepInfo } from './kernel-process/kernel-process-step-info'
import { KernelProcessStepMetadataAttribute } from './kernel-process/kernel-process-step-metadata'
import {
  KernelProcessStateMetadata,
  KernelProcessStepStateMetadata,
} from './kernel-process/kernel-process-step-state-metadata'
import { getGenericStateType } from './process-types'

/**
 * Extracts the process step metadata from the type.
 * @experimental
 * @param stepCls - The step class to extract metadata from
 * @returns The metadata attribute
 */
export function extractProcessStepMetadataFromType(
  stepCls: new (...args: any[]) => any
): KernelProcessStepMetadataAttribute {
  return (stepCls as any)._kernel_process_step_metadata || new KernelProcessStepMetadataAttribute({ version: 'v1' })
}

/**
 * Converts a kernel process to process state metadata.
 * @experimental
 * @param kernelProcess - The kernel process to convert
 * @returns The process state metadata
 */
export function kernelProcessToProcessStateMetadata(kernelProcess: KernelProcess): KernelProcessStateMetadata {
  const metadata = new KernelProcessStateMetadata({
    name: kernelProcess.state.name,
    id: kernelProcess.state.id,
    versionInfo: kernelProcess.state.version,
    stepsState: {},
  })

  for (const step of kernelProcess.steps) {
    metadata.stepsState[step.state.name] = toProcessStateMetadata(step)
  }

  return metadata
}

/**
 * Converts a step info object to process state metadata.
 * @experimental
 * @param stepInfo - The step info to convert
 * @returns The process state metadata
 */
export function toProcessStateMetadata(stepInfo: KernelProcessStepInfo): KernelProcessStepStateMetadata {
  // Check if stepInfo is actually a KernelProcess
  if ('steps' in stepInfo && Array.isArray((stepInfo as any).steps)) {
    return kernelProcessToProcessStateMetadata(stepInfo as any as KernelProcess)
  }

  return stepInfoToProcessStateMetadata(stepInfo)
}

/**
 * Converts a step info object to process state metadata.
 * @experimental
 * @param stepInfo - The step info to convert
 * @returns The step state metadata
 */
export function stepInfoToProcessStateMetadata(stepInfo: KernelProcessStepInfo): KernelProcessStepStateMetadata {
  const metadata = new KernelProcessStepStateMetadata({
    name: stepInfo.state.name,
    id: stepInfo.state.id,
    versionInfo: stepInfo.state.version,
  })

  const genericStateType = getGenericStateType(stepInfo.innerStepType)
  if (genericStateType) {
    const innerState = (stepInfo.state as any).state
    if (innerState !== null && innerState !== undefined) {
      metadata.state = innerState
    }
  }

  return metadata
}
