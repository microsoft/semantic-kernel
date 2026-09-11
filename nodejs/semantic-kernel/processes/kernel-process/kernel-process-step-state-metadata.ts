import { readFile } from 'fs/promises'
import { join, resolve } from 'path'
import { createDefaultLogger } from '../../utils/logger'

const logger = createDefaultLogger('KernelProcessStateMetadata')

/**
 * Process state used for State Persistence serialization.
 * @experimental
 */
export class KernelProcessStepStateMetadata<TState = any> {
  /**
   * The type of the metadata.
   */
  $type: 'Step' | 'Process' = 'Step'

  /**
   * The ID of the step.
   */
  id?: string | null = null

  /**
   * The name of the step.
   */
  name?: string | null = null

  /**
   * The version information.
   */
  versionInfo?: string | null = null

  /**
   * The state data.
   */
  state?: TState | null = null

  constructor(params?: {
    id?: string | null
    name?: string | null
    versionInfo?: string | null
    state?: TState | null
  }) {
    if (params) {
      if (params.id !== undefined) {
        this.id = params.id
      }
      if (params.name !== undefined) {
        this.name = params.name
      }
      if (params.versionInfo !== undefined) {
        this.versionInfo = params.versionInfo
      }
      if (params.state !== undefined) {
        this.state = params.state
      }
    }
  }
}

/**
 * Process state used for State Persistence serialization.
 * @experimental
 */
export class KernelProcessStateMetadata<TState = any> extends KernelProcessStepStateMetadata<TState> {
  /**
   * The type of the metadata.
   */
  override $type = 'Process' as const

  /**
   * The state of all steps in the process.
   */
  stepsState: Record<string, KernelProcessStateMetadata | KernelProcessStepStateMetadata> = {}

  constructor(params?: {
    id?: string | null
    name?: string | null
    versionInfo?: string | null
    state?: TState | null
    stepsState?: Record<string, KernelProcessStateMetadata | KernelProcessStepStateMetadata>
  }) {
    super(params)
    this.$type = 'Process' as const

    if (params?.stepsState !== undefined) {
      this.stepsState = params.stepsState
    }
  }

  /**
   * Loads a KernelProcessStateMetadata instance from a JSON file.
   * @param jsonFilename - Name of the JSON file to load
   * @param directory - Base directory where the file resides
   * @param encoding - Encoding to use when reading the file. Defaults to 'utf-8'
   * @returns Loaded process state metadata or null on failure
   */
  static async loadFromFile(
    jsonFilename: string,
    directory: string,
    encoding: BufferEncoding = 'utf-8'
  ): Promise<KernelProcessStateMetadata | null> {
    const filePath = resolve(join(directory, jsonFilename))

    try {
      const fileContents = await readFile(filePath, { encoding })
      const data = JSON.parse(fileContents)

      // Convert the plain object to a KernelProcessStateMetadata instance
      return new KernelProcessStateMetadata({
        id: data.id || data.$id,
        name: data.name,
        versionInfo: data.versionInfo,
        state: data.state,
        stepsState: data.stepsState || {},
      })
    } catch (error) {
      logger.error(`Error reading file '${filePath}':`, error)
      return null
    }
  }
}
