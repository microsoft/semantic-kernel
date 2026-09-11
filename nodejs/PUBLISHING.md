# Publishing the Semantic Kernel Package

This guide explains how to build and publish the `semantic-kernel` package to your artifactory or npm registry.

## Prerequisites

1. Node.js 18+ installed
2. npm or yarn package manager
3. Access credentials for your artifactory (if publishing to private registry)

## Configuration

### 1. Configure Artifactory Registry

Update the `.npmrc` file with your artifactory URL:

```bash
# .npmrc
registry=https://your-artifactory-url/artifactory/api/npm/npm-local/
```

### 2. Set Authentication

For artifactory, you'll need to authenticate. You can either:

**Option A: Using .npmrc with auth token**

```bash
# Add to .npmrc
//your-artifactory-url/artifactory/api/npm/npm-local/:_authToken=${NPM_TOKEN}
```

**Option B: Using npm login**

```bash
npm login --registry=https://your-artifactory-url/artifactory/api/npm/npm-local/
```

**Option C: Using environment variables**

```bash
export NPM_TOKEN=your-auth-token
```

## Building the Package

### 1. Install Dependencies

```bash
npm install
```

### 2. Build the Package

```bash
npm run build
```

This will:

- Clean the `dist` folder
- Compile TypeScript to JavaScript
- Generate type declarations (.d.ts files)
- Create source maps

### 3. Verify the Build

Check that the `dist` folder contains:

- `index.js` and `index.d.ts` (main entry point)
- `semantic-kernel/` folder with all compiled modules

## Publishing

### 1. Update Version

Update the version in `package.json`:

```bash
npm version patch  # for patch version bump (0.0.1 -> 0.0.2)
npm version minor  # for minor version bump (0.0.1 -> 0.1.0)
npm version major  # for major version bump (0.0.1 -> 1.0.0)
```

### 2. Publish to Artifactory

```bash
npm publish
```

Or if you want to see what will be published first:

```bash
npm publish --dry-run
```

### 3. Publishing to a Specific Registry

```bash
npm publish --registry https://your-artifactory-url/artifactory/api/npm/npm-local/
```

## Installing the Published Package

Once published, users can install the package:

```bash
npm install semantic-kernel
```

Or if using a private registry:

```bash
npm install semantic-kernel --registry=https://your-artifactory-url/artifactory/api/npm/npm-local/
```

## Package Structure

The published package includes:

```
semantic-kernel/
├── dist/
│   ├── index.js                    # Main entry point
│   ├── index.d.ts                  # Type definitions
│   └── semantic-kernel/            # All SDK modules
│       ├── kernel.js
│       ├── connectors/
│       ├── contents/
│       ├── functions/
│       └── ...
├── package.json
├── README.md
└── LICENSE
```

## Package Exports

The package provides multiple entry points:

- `semantic-kernel` - Main entry point
- `semantic-kernel/kernel` - Kernel module
- `semantic-kernel/connectors/ai/openai` - OpenAI connector
- `semantic-kernel/functions` - Functions module
- `semantic-kernel/contents` - Contents module

## Usage After Installation

```typescript
import { Kernel } from 'semantic-kernel'
import { OpenAIChatCompletion } from 'semantic-kernel/connectors/ai/openai'
import { ChatHistory } from 'semantic-kernel/contents'

const kernel = new Kernel()
const chatService = new OpenAIChatCompletion({ apiKey: 'your-key' })
kernel.addService('chat', chatService)
```

## Troubleshooting

### Build Errors

If you encounter build errors:

```bash
npm run clean
npm install
npm run build
```

### Authentication Issues

If publishing fails with authentication errors:

```bash
npm logout
npm login --registry=https://your-artifactory-url/artifactory/api/npm/npm-local/
```

### Version Conflicts

If the version already exists in the registry:

```bash
npm version patch
npm publish
```

## CI/CD Integration

For automated publishing in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Build and Publish
  run: |
    npm install
    npm run build
    npm publish --registry=${{ secrets.ARTIFACTORY_URL }}
  env:
    NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```
