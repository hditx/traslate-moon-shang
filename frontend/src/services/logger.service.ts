export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'

export interface LogEntry {
  timestamp: string
  level: LogLevel
  module: string
  message: string
  details?: unknown
}

const MAX_LOG_ENTRIES = 200

class LoggerService {
  private logs: LogEntry[] = []

  private log(level: LogLevel, module: string, message: string, details?: unknown) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      module,
      message,
      details,
    }

    this.logs.push(entry)
    if (this.logs.length > MAX_LOG_ENTRIES) {
      this.logs.shift()
    }

    const prefix = `[${entry.timestamp.substring(11, 19)}] [${level}] [${module}]:`
    const style = this.getStyleForLevel(level)

    if (details !== undefined) {
      // eslint-disable-next-line no-console
      console.log(`%c${prefix}`, style, message, details)
    } else {
      // eslint-disable-next-line no-console
      console.log(`%c${prefix}`, style, message)
    }
  }

  private getStyleForLevel(level: LogLevel): string {
    switch (level) {
      case 'DEBUG':
        return 'color: #94a3b8; font-weight: normal;'
      case 'INFO':
        return 'color: #38bdf8; font-weight: bold;'
      case 'WARN':
        return 'color: #facc15; font-weight: bold;'
      case 'ERROR':
        return 'color: #f87171; font-weight: bold;'
    }
  }

  debug(module: string, message: string, details?: unknown) {
    this.log('DEBUG', module, message, details)
  }

  info(module: string, message: string, details?: unknown) {
    this.log('INFO', module, message, details)
  }

  warn(module: string, message: string, details?: unknown) {
    this.log('WARN', module, message, details)
  }

  error(module: string, message: string, details?: unknown) {
    this.log('ERROR', module, message, details)
  }

  getLogs(): readonly LogEntry[] {
    return this.logs
  }

  clearLogs(): void {
    this.logs = []
  }
}

export const logger = new LoggerService()
