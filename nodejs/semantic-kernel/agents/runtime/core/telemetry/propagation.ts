import { context, Link, propagation, trace } from '@opentelemetry/api'

/**
 * Metadata for an envelope to support distributed tracing.
 */
export interface EnvelopeMetadata {
  traceparent?: string
  tracestate?: string
  links?: Link[]
}

/**
 * Type for telemetry metadata containers - either EnvelopeMetadata or a Record of strings.
 */
export type TelemetryMetadataContainer = EnvelopeMetadata | Record<string, string> | null | undefined

/**
 * Retrieves the telemetry envelope metadata from the current trace context.
 *
 * @returns The envelope metadata containing the traceparent and tracestate.
 */
export function getTelemetryEnvelopeMetadata(): EnvelopeMetadata {
  const carrier: Record<string, string> = {}
  propagation.inject(context.active(), carrier)

  return {
    traceparent: carrier['traceparent'],
    tracestate: carrier['tracestate'],
  }
}

/**
 * Retrieves the telemetry gRPC metadata with existing metadata merged.
 *
 * @param existingMetadata - The existing metadata to include in the gRPC metadata.
 * @returns The gRPC metadata containing the traceparent and tracestate.
 */
export function getTelemetryGrpcMetadata(existingMetadata?: Record<string, string>): Record<string, string> {
  const carrier: Record<string, string> = {}
  propagation.inject(context.active(), carrier)

  const metadata: Record<string, string> = { ...(existingMetadata || {}) }

  if (carrier['traceparent']) {
    metadata['traceparent'] = carrier['traceparent']
  }
  if (carrier['tracestate']) {
    metadata['tracestate'] = carrier['tracestate']
  }

  return metadata
}

/**
 * Gets the carrier for envelope metadata.
 */
function getCarrierForEnvelopeMetadata(envelopeMetadata: EnvelopeMetadata): Record<string, string> {
  const carrier: Record<string, string> = {}

  if (envelopeMetadata.traceparent) {
    carrier['traceparent'] = envelopeMetadata.traceparent
  }
  if (envelopeMetadata.tracestate) {
    carrier['tracestate'] = envelopeMetadata.tracestate
  }

  return carrier
}

/**
 * Gets the carrier for remote call metadata.
 */
function getCarrierForRemoteCallMetadata(remoteCallMetadata: Record<string, string>): Record<string, string> {
  const carrier: Record<string, string> = {}

  const traceparent = remoteCallMetadata['traceparent']
  const tracestate = remoteCallMetadata['tracestate']

  if (traceparent) {
    carrier['traceparent'] = traceparent
  }
  if (tracestate) {
    carrier['tracestate'] = tracestate
  }

  return carrier
}

/**
 * Retrieves the telemetry context from the given metadata.
 *
 * @param metadata - The metadata containing the telemetry context.
 * @returns The telemetry context extracted from the metadata.
 */
export function getTelemetryContext(metadata: TelemetryMetadataContainer): ReturnType<typeof context.active> {
  if (!metadata) {
    return context.active()
  }

  const carrier = isEnvelopeMetadata(metadata)
    ? getCarrierForEnvelopeMetadata(metadata)
    : getCarrierForRemoteCallMetadata(metadata)

  return propagation.extract(context.active(), carrier)
}

/**
 * Gets telemetry links from metadata for span linking.
 *
 * @param metadata - The metadata containing potential links.
 * @returns Array of links if available.
 */
export function getTelemetryLinks(metadata: TelemetryMetadataContainer): Link[] | undefined {
  if (!metadata) {
    return undefined
  }

  if (isEnvelopeMetadata(metadata) && metadata.links) {
    return metadata.links
  }

  // Create a link from the parent context
  const parentContext = getTelemetryContext(metadata)
  const span = trace.getSpan(parentContext)

  if (span) {
    const spanContext = span.spanContext()
    if (spanContext.traceId) {
      return [{ context: spanContext }]
    }
  }

  return undefined
}

/**
 * Type guard to check if metadata is EnvelopeMetadata.
 */
function isEnvelopeMetadata(metadata: TelemetryMetadataContainer): metadata is EnvelopeMetadata {
  if (!metadata) return false
  return 'traceparent' in metadata || 'tracestate' in metadata || 'links' in metadata
}
