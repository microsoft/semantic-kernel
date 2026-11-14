import { Attributes, context, Span, SpanKind, SpanOptions, trace, Tracer, TracerProvider } from '@opentelemetry/api'
import { experimental } from '../../../../utils/feature-stage-decorator'
import type { TelemetryMetadataContainer } from './propagation'
import { getTelemetryContext, getTelemetryLinks } from './propagation'
import type { TracingConfig } from './tracing-config'

/**
 * TraceHelper is a utility class to assist with tracing operations using OpenTelemetry.
 *
 * This class provides methods to create and manage spans for tracing operations,
 * following semantic conventions and supporting nested spans through metadata contexts.
 */
@experimental
export class TraceHelper<TOperation extends string, TDestination, TExtraAttributes extends Record<string, any>> {
  private tracerProvider: TracerProvider
  private tracer: Tracer
  private instrumentationBuilderConfig: TracingConfig<TOperation, TDestination, TExtraAttributes>

  constructor(
    tracerProvider: TracerProvider | null | undefined,
    instrumentationBuilderConfig: TracingConfig<TOperation, TDestination, TExtraAttributes>
  ) {
    // Evaluate in order: first try tracerProvider param, then get global tracer, finally fallback to NoOp
    this.tracerProvider = tracerProvider || trace.getTracerProvider()
    this.tracer = this.tracerProvider.getTracer(`agent_runtime ${instrumentationBuilderConfig.name}`)
    this.instrumentationBuilderConfig = instrumentationBuilderConfig
  }

  /**
   * Execute a function within a traced span.
   *
   * This is a thin wrapper that helps us:
   * 1. Follow semantic conventions
   * 2. Get contexts from metadata so we can get nested spans
   *
   * @param operation - The messaging operation being performed.
   * @param destination - The messaging destination being used.
   * @param parent - The parent telemetry metadata context.
   * @param fn - The function to execute within the span.
   * @param options - Additional span options.
   * @returns The result of the function execution.
   */
  async traceBlock<T>(
    operation: TOperation,
    destination: TDestination,
    parent: TelemetryMetadataContainer,
    fn: (span: Span) => Promise<T>,
    options?: {
      extraAttributes?: TExtraAttributes
      kind?: SpanKind
      attributes?: Attributes
      startTime?: number
      recordException?: boolean
      setStatusOnException?: boolean
      endOnExit?: boolean
    }
  ): Promise<T> {
    const spanName = this.instrumentationBuilderConfig.getSpanName(operation, destination)
    const spanKind = options?.kind || this.instrumentationBuilderConfig.getSpanKind(operation)
    const parentContext = parent ? getTelemetryContext(parent) : context.active()
    const links = parent ? getTelemetryLinks(parent) : undefined

    const attributesWithDefaults: Attributes = { ...(options?.attributes || {}) }
    const instrumentationAttributes = this.instrumentationBuilderConfig.buildAttributes(
      operation,
      destination,
      options?.extraAttributes
    )

    Object.assign(attributesWithDefaults, instrumentationAttributes)

    const spanOptions: SpanOptions = {
      kind: spanKind,
      attributes: attributesWithDefaults,
      links,
      startTime: options?.startTime,
    }

    const span = this.tracer.startSpan(spanName, spanOptions, parentContext)

    try {
      return await context.with(trace.setSpan(parentContext, span), async () => {
        return await fn(span)
      })
    } catch (error) {
      if (options?.recordException !== false) {
        span.recordException(error as Error)
      }
      if (options?.setStatusOnException !== false) {
        span.setStatus({
          code: 2, // ERROR
          message: (error as Error).message,
        })
      }
      throw error
    } finally {
      if (options?.endOnExit !== false) {
        span.end(options?.startTime ? Date.now() : undefined)
      }
    }
  }

  /**
   * Synchronous version of traceBlock for non-async operations.
   */
  traceBlockSync<T>(
    operation: TOperation,
    destination: TDestination,
    parent: TelemetryMetadataContainer,
    fn: (span: Span) => T,
    options?: {
      extraAttributes?: TExtraAttributes
      kind?: SpanKind
      attributes?: Attributes
      startTime?: number
      recordException?: boolean
      setStatusOnException?: boolean
      endOnExit?: boolean
    }
  ): T {
    const spanName = this.instrumentationBuilderConfig.getSpanName(operation, destination)
    const spanKind = options?.kind || this.instrumentationBuilderConfig.getSpanKind(operation)
    const parentContext = parent ? getTelemetryContext(parent) : context.active()
    const links = parent ? getTelemetryLinks(parent) : undefined

    const attributesWithDefaults: Attributes = { ...(options?.attributes || {}) }
    const instrumentationAttributes = this.instrumentationBuilderConfig.buildAttributes(
      operation,
      destination,
      options?.extraAttributes
    )

    Object.assign(attributesWithDefaults, instrumentationAttributes)

    const spanOptions: SpanOptions = {
      kind: spanKind,
      attributes: attributesWithDefaults,
      links,
      startTime: options?.startTime,
    }

    const span = this.tracer.startSpan(spanName, spanOptions, parentContext)

    try {
      return context.with(trace.setSpan(parentContext, span), () => {
        return fn(span)
      })
    } catch (error) {
      if (options?.recordException !== false) {
        span.recordException(error as Error)
      }
      if (options?.setStatusOnException !== false) {
        span.setStatus({
          code: 2, // ERROR
          message: (error as Error).message,
        })
      }
      throw error
    } finally {
      if (options?.endOnExit !== false) {
        span.end(options?.startTime ? Date.now() : undefined)
      }
    }
  }
}
