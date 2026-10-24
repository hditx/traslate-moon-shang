import { describe, it, expect, beforeEach, vi } from 'vitest'
import { logger } from '@/services/logger.service'

describe('LoggerService', () => {
  beforeEach(() => {
    logger.clearLogs()
    vi.restoreAllMocks()
  })

  it('records logs with levels, modules and timestamps', () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

    logger.info('testModule', 'Operación exitosa', { count: 5 })
    logger.warn('testModule', 'Advertencia leve')
    logger.error('testModule', 'Error crítico')
    logger.debug('testModule', 'Detalle de depuración')

    const logs = logger.getLogs()
    expect(logs).toHaveLength(4)
    expect(logs[0].level).toBe('INFO')
    expect(logs[0].message).toBe('Operación exitosa')
    expect(logs[0].details).toEqual({ count: 5 })
    expect(logs[1].level).toBe('WARN')
    expect(logs[2].level).toBe('ERROR')
    expect(logs[3].level).toBe('DEBUG')
    expect(consoleSpy).toHaveBeenCalledTimes(4)
  })

  it('respects ring buffer maximum size without unbounded memory growth', () => {
    vi.spyOn(console, 'log').mockImplementation(() => {})

    for (let i = 0; i < 250; i++) {
      logger.info('bulk', `Mensaje ${i}`)
    }

    const logs = logger.getLogs()
    expect(logs.length).toBe(200)
    // El primer mensaje debe ser 50 (los primeros 50 fueron descartados por el ring buffer)
    expect(logs[0].message).toBe('Mensaje 50')
    expect(logs[199].message).toBe('Mensaje 249')
  })

  it('clears logs when clearLogs is called', () => {
    vi.spyOn(console, 'log').mockImplementation(() => {})

    logger.info('test', 'Mensaje 1')
    expect(logger.getLogs()).toHaveLength(1)

    logger.clearLogs()
    expect(logger.getLogs()).toHaveLength(0)
  })
})
