/**
 * TimePlugin provides a set of functions to get the current time and date.
 *
 * Usage:
 *     kernel.addPlugin(new TimePlugin(), { pluginName: "time" })
 *
 * Examples:
 *     {{time.date}}            => Sunday, 12 January, 2031
 *     {{time.today}}           => Sunday, 12 January, 2031
 *     {{time.isoDate}}         => 2031-01-12
 *     {{time.now}}             => Sunday, January 12, 2031 9:15 PM
 *     {{time.utcNow}}          => Sunday, January 13, 2031 5:15 AM
 *     {{time.time}}            => 09:15:07 PM
 *     {{time.year}}            => 2031
 *     {{time.month}}           => January
 *     {{time.monthNumber}}     => 01
 *     {{time.day}}             => 12
 *     {{time.dayOfWeek}}       => Sunday
 *     {{time.hour}}            => 9 PM
 *     {{time.hourNumber}}      => 21
 *     {{time.daysAgo $days}}   => Sunday, 7 May, 2023
 *     {{time.dateMatchingLastDayName $dayName}} => Sunday, 7 May, 2023
 *     {{time.minute}}          => 15
 *     {{time.second}}          => 7
 *     {{time.timeZoneOffset}}  => -08:00
 *     {{time.timeZoneName}}    => PST
 */
export class TimePlugin {
  /**
   * Get the current date.
   *
   * Example:
   *     {{time.date}} => Sunday, 12 January, 2031
   */
  date(): string {
    const now = new Date()
    return now.toLocaleDateString('en-US', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    })
  }

  /**
   * Get the current date.
   *
   * Example:
   *     {{time.today}} => Sunday, 12 January, 2031
   */
  today(): string {
    return this.date()
  }

  /**
   * Get the current date in ISO format.
   *
   * Example:
   *     {{time.isoDate}} => 2031-01-12
   */
  isoDate(): string {
    const today = new Date()
    return today.toISOString().split('T')[0]
  }

  /**
   * Get the current date and time in the local time zone.
   *
   * Example:
   *     {{time.now}} => Sunday, January 12, 2031 9:15 PM
   */
  now(): string {
    const now = new Date()
    const dateStr = now.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    })
    const timeStr = now.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
    return `${dateStr} ${timeStr}`
  }

  /**
   * Get the current date and time in UTC.
   *
   * Example:
   *     {{time.utcNow}} => Sunday, January 13, 2031 5:15 AM
   */
  utcNow(): string {
    const now = new Date()
    const dateStr = now.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      timeZone: 'UTC',
    })
    const timeStr = now.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      timeZone: 'UTC',
    })
    return `${dateStr} ${timeStr}`
  }

  /**
   * Get the current time in the local time zone.
   *
   * Example:
   *     {{time.time}} => 09:15:07 PM
   */
  time(): string {
    const now = new Date()
    return now.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    })
  }

  /**
   * Get the current year.
   *
   * Example:
   *     {{time.year}} => 2031
   */
  year(): string {
    const now = new Date()
    return now.getFullYear().toString()
  }

  /**
   * Get the current month.
   *
   * Example:
   *     {{time.month}} => January
   */
  month(): string {
    const now = new Date()
    return now.toLocaleDateString('en-US', { month: 'long' })
  }

  /**
   * Get the current month number.
   *
   * Example:
   *     {{time.monthNumber}} => 01
   */
  monthNumber(): string {
    const now = new Date()
    return (now.getMonth() + 1).toString().padStart(2, '0')
  }

  /**
   * Get the current day of the month.
   *
   * Example:
   *     {{time.day}} => 12
   */
  day(): string {
    const now = new Date()
    return now.getDate().toString().padStart(2, '0')
  }

  /**
   * Get the current day of the week.
   *
   * Example:
   *     {{time.dayOfWeek}} => Sunday
   */
  dayOfWeek(): string {
    const now = new Date()
    return now.toLocaleDateString('en-US', { weekday: 'long' })
  }

  /**
   * Get the current hour.
   *
   * Example:
   *     {{time.hour}} => 9 PM
   */
  hour(): string {
    const now = new Date()
    return now.toLocaleTimeString('en-US', {
      hour: 'numeric',
      hour12: true,
    })
  }

  /**
   * Get the current hour number.
   *
   * Example:
   *     {{time.hourNumber}} => 21
   */
  hourNumber(): string {
    const now = new Date()
    return now.getHours().toString().padStart(2, '0')
  }

  /**
   * Get the current minute.
   *
   * Example:
   *     {{time.minute}} => 15
   */
  minute(): string {
    const now = new Date()
    return now.getMinutes().toString().padStart(2, '0')
  }

  /**
   * Get the date a provided number of days in the past.
   *
   * @param days - The number of days to offset from today
   * @returns The date of the offset day
   *
   * Example:
   *     {{time.daysAgo $input}} => Sunday, 7 May, 2023
   */
  daysAgo(days: string): string {
    const daysNum = parseInt(days, 10)
    const d = new Date()
    d.setDate(d.getDate() - daysNum)
    return d.toLocaleDateString('en-US', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    })
  }

  /**
   * Get the date of the last day matching the supplied day name.
   *
   * @param dayName - The day name to match with
   * @returns The date of the matching day
   *
   * Example:
   *     {{time.dateMatchingLastDayName $input}} => Sunday, 7 May, 2023
   */
  dateMatchingLastDayName(dayName: string): string {
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    const targetDay = dayNames.indexOf(dayName)

    if (targetDay === -1) {
      throw new Error('day_name is not recognized')
    }

    const d = new Date()
    for (let i = 1; i <= 7; i++) {
      d.setDate(d.getDate() - 1)
      if (d.getDay() === targetDay) {
        return d.toLocaleDateString('en-US', {
          weekday: 'long',
          day: '2-digit',
          month: 'long',
          year: 'numeric',
        })
      }
    }

    throw new Error('day_name is not recognized')
  }

  /**
   * Get the seconds on the current minute.
   *
   * Example:
   *     {{time.second}} => 7
   */
  second(): string {
    const now = new Date()
    return now.getSeconds().toString().padStart(2, '0')
  }

  /**
   * Get the current time zone offset.
   *
   * Example:
   *     {{time.timeZoneOffset}} => -08:00
   */
  timeZoneOffset(): string {
    const now = new Date()
    const offset = -now.getTimezoneOffset()
    const hours = Math.floor(Math.abs(offset) / 60)
    const minutes = Math.abs(offset) % 60
    const sign = offset >= 0 ? '+' : '-'
    return `${sign}${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
  }

  /**
   * Get the current time zone name.
   *
   * Example:
   *     {{time.timeZoneName}} => PST
   */
  timeZoneName(): string {
    const now = new Date()
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone
    const tzName = now.toLocaleTimeString('en-US', {
      timeZoneName: 'short',
    })
    const match = tzName.match(/\b([A-Z]{2,5})\b/)
    return match ? match[1] : timeZone
  }
}
