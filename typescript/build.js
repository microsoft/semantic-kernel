#!/usr/bin/env node

import { build } from 'esbuild';
import { readFile, writeFile } from 'fs/promises';
import { join } from 'path';

const sharedConfig = {
  entryPoints: ['src/index.ts'],
  bundle: true,
  sourcemap: true,
  platform: 'node',
  target: 'node18',
  external: ['openai', 'zod', '@opentelemetry/api'],
  minify: false,
};

async function buildAll() {
  console.log('Building CommonJS bundle...');
  await build({
    ...sharedConfig,
    format: 'cjs',
    outfile: 'dist/index.cjs',
  });

  console.log('Building ESM bundle...');
  await build({
    ...sharedConfig,
    format: 'esm',
    outfile: 'dist/index.mjs',
  });

  // Create package.json for ESM support
  console.log('Creating package.json for dual package support...');
  const packageJson = JSON.parse(await readFile('package.json', 'utf8'));
  
  const distPackageJson = {
    name: packageJson.name,
    version: packageJson.version,
    main: './index.cjs',
    module: './index.mjs',
    types: './index.d.ts',
    exports: {
      '.': {
        import: './index.mjs',
        require: './index.cjs',
        types: './index.d.ts'
      }
    }
  };

  await writeFile(
    join('dist', 'package.json'),
    JSON.stringify(distPackageJson, null, 2)
  );

  console.log('Build complete!');
}

buildAll().catch(console.error);