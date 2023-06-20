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

/*
 * Function to render the date and/or time of a message.
 */
export function timestampToDateString(timestamp: number, alwaysShowTime = false) {
    const date = new Date(timestamp);
    const dateString = date.toLocaleDateString([], {
        month: 'numeric',
        day: 'numeric',
    });
    const timeString = date.toLocaleTimeString([], {
        hour: 'numeric',
        minute: '2-digit',
    });

    return date.toDateString() !== new Date().toDateString()
        ? alwaysShowTime
            ? dateString + ' ' + timeString // if the date is not today and we are always showing the time, show the date and time
            : dateString // if the date is not today and we are not always showing the time, only show the date
        : timeString; // if the date is today, only show the time
}
