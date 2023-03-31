import replace from '@rollup/plugin-replace';
import react from '@vitejs/plugin-react';
import fs from 'fs';
import path from 'path';
import { defineConfig, PluginOption } from 'vite';
import mkcert from 'vite-plugin-mkcert';
// import { VitePWAOptions } from 'vite-plugin-pwa';

const packageJson = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'package.json'), 'utf8'));
const dateString = new Date().toISOString().replace('T', ' @ ').replace(/\..+/, '');
const appVersion = `${packageJson.version as string} (${dateString})`;
const replaceOptions = { __APP_VERSION__: appVersion };

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        react(),
        // VitePWA(pwaOptions),
        replace(replaceOptions),
        mkcert({
            savePath: 'certs',
            keyFileName: 'key.pem',
            certFileName: 'cert.pem',
        }),
    ] as PluginOption[],
    server: {
        https: true,
        host: 'localhost',
        port: 3000,
    },
    build: {
        sourcemap: true,
    },
});
