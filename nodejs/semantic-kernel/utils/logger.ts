import winston from 'winston'

// Logger configuration options
export interface LoggerOptions {
  level?: string
  formatType?: 'pretty' | 'json'
  format?: winston.Logform.Format
  transports?: winston.transport[]
  silent?: boolean
}

/**
 * Creates a default Winston logger for the Kernel
 */
export function createDefaultLogger(aggregation?: string, options?: LoggerOptions): winston.Logger {
  const isPretty = options?.formatType === 'pretty'

  const agg = aggregation ? formatAgg(aggregation) : 'semantic-kernel'

  // 1. Define the base common formats
  const baseFormats = [
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
  ]

  // 2. Add the final output format (JSON or Pretty)
  const finalFormat = isPretty
    ? winston.format.printf(({ level, message, timestamp, stack, ...meta }) => {
        const baseMessage = `agg:${agg} ${timestamp} [${level.toUpperCase()}]: ${message}`
        const metadata = Object.keys(meta).length ? `\n${JSON.stringify(meta)}` : ''
        return stack ? `${baseMessage}\n${stack}` : `${baseMessage}${metadata}`
      })
    : winston.format.json()

  const defaultFormat = winston.format.combine(...baseFormats, finalFormat)

  const processLogLevel = ['info', 'warn', 'error', 'debug'].includes(process.env.LOG_LEVEL || '')
    ? process.env.LOG_LEVEL
    : undefined

  return winston.createLogger({
    level: options?.level || processLogLevel || 'info',
    defaultMeta: { agg },
    format: options?.format || defaultFormat,
    transports: options?.transports || [
      new winston.transports.Console({
        // Only use colorize() if isPretty is true
        format: isPretty ? winston.format.combine(winston.format.colorize(), defaultFormat) : defaultFormat,
      }),
    ],
    silent: options?.silent || false,
  })
}

const formatAgg = (str: string) =>
  str
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/([A-Z])([A-Z][a-z])/g, '$1-$2')
    .toLowerCase()

export type Logger = winston.Logger
