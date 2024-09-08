export class CodeFixMapping
{
	// The Diagnostic Type is declared from a different context but we can pass them this way
	diagnostic: any;
	replacement: string;
	fileName: string;
	friendlyString: string;
	matchStart: string;
	matchEnd: string;
	isSuppression: boolean;
	version: number;
	constructor(diagnostic: any, replacement: string, fileName: string, friendlyString: string, matchStart: string, matchEnd: string, isSuppression: boolean, version: number)
	{
		this.diagnostic = diagnostic;
		this.replacement = replacement;
		this.fileName = fileName;
		this.friendlyString = friendlyString;
		this.matchStart = matchStart;
		this.matchEnd = matchEnd;
		this.isSuppression = isSuppression;
		this.version = version;
	}
}