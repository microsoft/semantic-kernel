import * as nbgv from 'nerdbank-gitversioning';
import * as cp from 'child_process';

const versionInfo = await nbgv.getVersion();
// check that versionInfo.simpleVersion is a valid version formatted like x.y.z
if (!versionInfo.simpleVersion.match(/^\d+\.\d+\.\d+$/)) {
	throw new Error(`Unexpected version format: ${versionInfo.simpleVersion}`);
}
console.log(`Setting package version to ${versionInfo.simpleVersion}`);
cp.execSync(`npm version ${versionInfo.simpleVersion}`);