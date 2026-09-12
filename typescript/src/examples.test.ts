import { describe, test, expect, beforeEach } from '@jest/globals';
import { Kernel } from '../src/kernel.js';
import { TimePlugin } from '../examples/plugins/TimePlugin.js';
import { WeatherPlugin } from '../examples/plugins/WeatherPlugin.js';
import { InMemoryVectorStore } from '../src/memory.js';
import { Context } from '../src/context.js';

describe('Examples Functionality', () => {
  let kernel: Kernel;

  beforeEach(() => {
    kernel = new Kernel();
  });

  test('TimePlugin functions work correctly', async () => {
    const timePlugin = new TimePlugin();
    kernel.addPlugin(timePlugin, 'time');

    // Test getCurrentTimeUtc
    const timeFunc = kernel.getFunction('time', 'getCurrentTimeUtc');
    expect(timeFunc).toBeDefined();
    
    const utcTime = await timeFunc!.invoke(new Context(kernel, {}));
    expect(typeof utcTime).toBe('string');
    expect(utcTime).toMatch(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z/);

    // Test getCurrentTimeWithOffset
    const offsetFunc = kernel.getFunction('time', 'getCurrentTimeWithOffset');
    expect(offsetFunc).toBeDefined();
    
    const offsetTime = await offsetFunc!.invoke(new Context(kernel, { offsetHours: 1 }));
    expect(typeof offsetTime).toBe('string');
    expect(offsetTime).toMatch(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z/);

    // Test getDayOfWeek
    const dayFunc = kernel.getFunction('time', 'getDayOfWeek');
    expect(dayFunc).toBeDefined();
    
    const dayOfWeek = await dayFunc!.invoke(new Context(kernel, {}));
    expect(typeof dayOfWeek).toBe('string');
    expect(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']).toContain(dayOfWeek);
  });

  test('WeatherPlugin functions work correctly', async () => {
    const weatherPlugin = new WeatherPlugin();
    kernel.addPlugin(weatherPlugin, 'weather');

    // Test getCurrentWeather
    const weatherFunc = kernel.getFunction('weather', 'getCurrentWeather');
    expect(weatherFunc).toBeDefined();
    
    const weather = await weatherFunc!.invoke(new Context(kernel, { location: 'New York' }));
    expect(typeof weather).toBe('string');
    
    const weatherData = JSON.parse(weather);
    expect(weatherData).toHaveProperty('location');
    expect(weatherData).toHaveProperty('temperature');
    expect(weatherData).toHaveProperty('condition');
    expect(weatherData.location).toBe('New York');

    // Test getWeatherForecast
    const forecastFunc = kernel.getFunction('weather', 'getWeatherForecast');
    expect(forecastFunc).toBeDefined();
    
    const forecast = await forecastFunc!.invoke(new Context(kernel, { location: 'London', days: '5' }));
    expect(typeof forecast).toBe('string');
    
    const forecastData = JSON.parse(forecast);
    expect(forecastData).toHaveProperty('location');
    expect(forecastData).toHaveProperty('forecast');
    expect(forecastData.forecast).toHaveLength(5);
  });

  test('Memory store functionality works', async () => {
    const memoryStore = new InMemoryVectorStore();
    kernel.registerMemoryStore(memoryStore);

    // Test collection creation
    await memoryStore.createCollection('test');
    expect(await memoryStore.doesCollectionExist('test')).toBe(true);

    // Test upsert and retrieval
    const testRecord = {
      id: 'test-1',
      embedding: [1, 0, 0, 0, 0],
      metadata: { text: 'test document' }
    };

    await memoryStore.upsert('test', testRecord);
    const retrieved = await memoryStore.get('test', 'test-1');
    expect(retrieved).toEqual(testRecord);

    // Test nearest matches
    const queryEmbedding = [0.9, 0.1, 0, 0, 0];
    const matches = await memoryStore.getNearestMatches('test', queryEmbedding, 1);
    expect(matches).toHaveLength(1);
    expect(matches[0].id).toBe('test-1');
  });

  test('Examples script configuration exists', () => {
    const packageJson = require('../package.json');
    expect(packageJson.scripts).toHaveProperty('examples');
    expect(packageJson.scripts).toHaveProperty('examples:01');
    expect(packageJson.scripts).toHaveProperty('examples:02');
    expect(packageJson.scripts).toHaveProperty('examples:03');
    expect(packageJson.scripts).toHaveProperty('examples:04');
    expect(packageJson.scripts).toHaveProperty('examples:05');
    expect(packageJson.scripts).toHaveProperty('examples:06');
    expect(packageJson.scripts).toHaveProperty('examples:07');
    expect(packageJson.scripts).toHaveProperty('examples:08');
  });
});