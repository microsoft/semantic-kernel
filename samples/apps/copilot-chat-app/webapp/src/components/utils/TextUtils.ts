/*
 * Function to detect and convert URLs within a string into clickable links.
 * It wraps each link matched with anchor tags and applies safe href attributes.
 */
export function convertToAnchorTags(htmlString: string) {
    // Regular expression to match links, excluding any HTML tags at the end
    // Since response from bot is plain text, sometimes line breaks and other html tags are included in the response for readability.
    var linkRegex = /(?:https?):\/\/(\w+:?\w*)?(\S+)(:\d+)?(\/|\/([\w#!:.?+=&%!\-/]))?(?=(<br|<p|<div|<span)\s*\/>|$)/g;

    var result = htmlString.replace(linkRegex, function (link) {
        // Parse URL first -- URL class handles cybersecurity concerns related to URL parsing and manipulation
        const safeHref = new URL(link).toString();

        // Replace each link with anchor tags
        return `<a href="${safeHref}">${link}</a>`;
    });

    return result;
}
