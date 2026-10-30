import { Attributes, SpanKind } from '@opentelemetry/api'
import { experimental } from '../../../../utils/feature-stage-decorator'
import type { AgentId } from '../agent-id'
import type { TopicId } from '../topic'

export const NAMESPACE = 'semantic-kernel.agent-runtime'

/**
 * Messaging operations for telemetry.
 */
export type MessagingOperation = 'create' | 'send' | 'publish' | 'receive' | 'intercept' | 'process' | 'ack'

/**
 * Messaging destinations for telemetry.
 */
export type MessagingDestination = AgentId | TopicId | string | null

/**
 * Extra attributes for message runtime instrumentation.
 */
export interface ExtraMessageRuntimeAttributes {
  messageSize?: number
  messageType?: string
}

/**
 * Abstract base class for tracing configuration.
 */
@experimental
export abstract class TracingConfig<
  TOperation extends string,
  TDestination,
  TExtraAttributes extends Record<string, any>,
> {
  /**
   * Gets the name of the module being instrumented.
   */
  abstract get name(): string

  /**
   * Builds the attributes for the instrumentation configuration.
   */
  abstract buildAttributes(
    operation: TOperation,
    destination: TDestination,
    extraAttributes?: TExtraAttributes
  ): Attributes

  /**
   * Returns the span name based on the given operation and destination.
   */
  abstract getSpanName(operation: TOperation, destination: TDestination): string

  /**
   * Determines the span kind based on the given messaging operation.
   */
  abstract getSpanKind(operation: TOperation): SpanKind
}

/**
 * Configuration for message runtime instrumentation.
 */
@experimental
export class MessageRuntimeTracingConfig extends TracingConfig<
  MessagingOperation,
  MessagingDestination,
  ExtraMessageRuntimeAttributes
> {
  private _runtimeName: string

  constructor(runtimeName: string) {
    super()
    this._runtimeName = runtimeName
  }

  get name(): string {
    return this._runtimeName
  }

  buildAttributes(
    operation: MessagingOperation,
    destination: MessagingDestination,
    extraAttributes?: ExtraMessageRuntimeAttributes
  ): Attributes {
    const attrs: Attributes = {
      'messaging.operation': this._getOperationType(operation),
      'messaging.destination': this._getDestinationStr(destination),
    }

    if (extraAttributes) {
      if (extraAttributes.messageSize !== undefined) {
        attrs['messaging.message.envelope.size'] = extraAttributes.messageSize
      }
      if (extraAttributes.messageType) {
        attrs['messaging.message.type'] = extraAttributes.messageType
      }
    }

    return attrs
  }

  getSpanName(operation: MessagingOperation, destination: MessagingDestination): string {
    const spanParts: string[] = [operation]
    const destinationStr = this._getDestinationStr(destination)

    if (destinationStr) {
      spanParts.push(destinationStr)
    }

    const spanName = spanParts.join(' ')
    return `${NAMESPACE} ${spanName}`
  }

  getSpanKind(operation: MessagingOperation): SpanKind {
    if (['create', 'send', 'publish'].includes(operation)) {
      return SpanKind.PRODUCER
    }
    if (['receive', 'intercept', 'process', 'ack'].includes(operation)) {
      return SpanKind.CONSUMER
    }
    return SpanKind.CLIENT
  }

  private _getDestinationStr(destination: MessagingDestination): string {
    if (!destination) {
      return ''
    }

    if (typeof destination === 'string') {
      return destination
    }

    // Check if it's an AgentId
    if ('type' in destination && 'key' in destination && !('source' in destination)) {
      return `${destination.type}.(${destination.key})-A`
    }

    // Check if it's a TopicId
    if ('type' in destination && 'source' in destination) {
      return `${destination.type}.(${destination.source})-T`
    }

    return ''
  }

  private _getOperationType(operation: MessagingOperation): string {
    if (['send', 'publish'].includes(operation)) {
      return 'publish'
    }
    if (operation === 'create') {
      return 'create'
    }
    if (['receive', 'intercept', 'ack'].includes(operation)) {
      return 'receive'
    }
    if (operation === 'process') {
      return 'process'
    }
    return 'Unknown'
  }
}
