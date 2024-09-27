import * as nbgv from 'nerdbank-gitversioning';
import { exit } from 'process';

async function isPreRelease() {
	var versionInfo = await nbgv.getVersion();
	const prereleaseTag = versionInfo.prereleaseVersionNoLeadingHyphen;
	if (!prereleaseTag) {
		return false;
	} 
	return true;
};

// This script exits with a 0 return code if a pre-release version is detected, or a non-zero exit code if release version is detected.
if (await isPreRelease())
{
	console.log("Detected Pre-Release");
	exit(0);
}
else{
	console.log("Detected Release");
	exit(-1);
}