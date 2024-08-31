export class FileVersion
{
	fileName: string;
	version: number;
	constructor(fileName: string, version: number)
	{
		this.fileName = fileName;
		this.version = version;
	}
}