import { experimental } from '../../feature-stage-decorator'

/**
 * Settings for model diagnostics.
 *
 * The settings are first loaded from environment variables with
 * the prefix 'SEMANTICKERNEL_EXPERIMENTAL_GENAI_'.
 *
 * Required settings for prefix 'SEMANTICKERNEL_EXPERIMENTAL_GENAI_' are:
 * - enable_otel_diagnostics: bool - Enable OpenTelemetry diagnostics. Default is false.
 *               (Env var SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS)
 * - enable_otel_diagnostics_sensitive: bool - Enable OpenTelemetry sensitive events. Default is false.
 *               (Env var SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE)
 */
@experimental
export class ModelDiagnosticSettings {
  enableOtelDiagnostics: boolean
  enableOtelDiagnosticsSensitive: boolean

  constructor() {
    this.enableOtelDiagnostics = this.getBooleanEnvVar(
      'SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS',
      false
    )
    this.enableOtelDiagnosticsSensitive = this.getBooleanEnvVar(
      'SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE',
      false
    )
  }

  private getBooleanEnvVar(name: string, defaultValue: boolean): boolean {
    const value = process.env[name]
    if (value === undefined || value === null || value === '') {
      return defaultValue
    }
    return value.toLowerCase() === 'true' || value === '1'
  }
}
