import { Context } from '../../src/context.js';

/**
 * TimePlugin provides time-related functions for the kernel
 */
export class TimePlugin {
  async getCurrentTimeUtc(context: Context): Promise<string> {
    const now = new Date();
    return now.toISOString();
  }

  async getCurrentTimeWithOffset(context: Context): Promise<string> {
    const { offsetHours } = context.variables;
    const now = new Date();
    const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
    const targetTime = new Date(utcTime + (offsetHours * 3600000));
    return targetTime.toISOString();
  }

  async getDayOfWeek(context: Context): Promise<string> {
    const now = new Date();
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[now.getDay()];
  }
}