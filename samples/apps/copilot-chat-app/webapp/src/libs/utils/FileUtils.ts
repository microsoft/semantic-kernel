// Function that fetches and parses the JSON file
export const fetchJson = async (filePath: URL): Promise<Response> => {
    try {
        // Make a GET request to the file URL
        const response = await fetch(filePath);

        if (response.ok) {
            return response;
        } else {
            throw new Error(`Failed to fetch ${filePath.toString()}: ${response.status}`);
        }
    } catch (err) {
        throw new Error(`Failed to fetch ${filePath.toString()}`);
    }
};
