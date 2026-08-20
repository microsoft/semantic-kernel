import { Context } from '../../src/context.js';

/**
 * WeatherPlugin provides weather-related functions for the kernel
 */
export class WeatherPlugin {
  async getCurrentWeather(context: Context): Promise<string> {
    const { location } = context.variables;
    
    // Mock weather data - in real implementation this would call a weather API
    const mockWeatherData: Record<string, { temperature: number; condition: string; humidity: number }> = {
      'new york': { temperature: 22, condition: 'sunny', humidity: 65 },
      'london': { temperature: 15, condition: 'cloudy', humidity: 78 },
      'tokyo': { temperature: 28, condition: 'partly cloudy', humidity: 70 },
      'paris': { temperature: 18, condition: 'rainy', humidity: 85 },
      'default': { temperature: 20, condition: 'unknown', humidity: 60 }
    };
    
    const key = location?.toLowerCase() || 'default';
    const weather = mockWeatherData[key] || mockWeatherData['default'];
    
    return JSON.stringify({
      location: location || 'Unknown Location',
      temperature: weather.temperature,
      condition: weather.condition,
      humidity: weather.humidity,
      unit: 'celsius'
    });
  }

  async getWeatherForecast(context: Context): Promise<string> {
    const { location, days } = context.variables;
    const daysCount = parseInt(days) || 3;
    
    // Mock forecast data
    const forecast = [];
    for (let i = 0; i < daysCount; i++) {
      const date = new Date();
      date.setDate(date.getDate() + i);
      forecast.push({
        date: date.toISOString().split('T')[0],
        temperature: 20 + Math.floor(Math.random() * 10),
        condition: ['sunny', 'cloudy', 'rainy'][Math.floor(Math.random() * 3)],
        humidity: 60 + Math.floor(Math.random() * 30)
      });
    }
    
    return JSON.stringify({
      location: location || 'Unknown Location',
      forecast
    });
  }
}