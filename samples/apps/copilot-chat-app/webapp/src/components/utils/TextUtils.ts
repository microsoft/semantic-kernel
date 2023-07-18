/*
 * Function to detect and convert URLs within a string into clickable links.
 * It wraps each link matched with anchor tags and applies safe href attributes.
 */
export function convertToAnchorTags(htmlString: string) {
    // Regular expression to match links, excluding any HTML tags at the end
    // Since response from bot is plain text, sometimes line breaks and other html tags are included in the response for readability.
    const linkRegex =
        /(?:https?):\/\/(\w+:?\w*)?(\S+)(:\d+)?(\/|\/([\w#!:.?+=&%!\-/]))?(?=(<br|<p|<div|<span)\s*\/>|$)/g;

    const result = htmlString.replace(linkRegex, function (link) {
        // Parse URL first -- URL class handles cybersecurity concerns related to URL parsing and manipulation
        const safeHref = new URL(link).toString();

        // Replace each link with anchor tags
        return `<a href="${safeHref}">${link}</a>`;
    });

    return result;
}

/*
 * Function to check if date is today.
 */
export function isToday(date: Date) {
    return date.toDateString() !== new Date().toDateString();
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

    return isToday(date)
        ? alwaysShowTime
            ? dateString + ' ' + timeString // if the date is not today and we are always showing the time, show the date and time
            : dateString // if the date is not today and we are not always showing the time, only show the date
        : timeString; // if the date is today, only show the time
}

/*
 * Function to create a command link
 */
export function createCommandLink(command: string) {
    const escapedCommand = encodeURIComponent(command);
    const createCommandLink = `<span style="text-decoration: underline; cursor: pointer" data-command="${escapedCommand}" onclick="(function(){ let chatInput = document.getElementById('chat-input'); chatInput.value = decodeURIComponent('${escapedCommand}'); chatInput.focus(); return false; })();return false;">${command}</span>`;
    return createCommandLink;
}

/*
 * Function to format chat text content to remove any html tags from it.
 */
export function formatChatTextContent(messageContent: string) {
    const contentAsString = messageContent
        .trim()
        .replace(/^sk:\/\/.*$/gm, (match: string) => createCommandLink(match))
        .replace(/^!sk:.*$/gm, (match: string) => createCommandLink(match));
    return contentAsString;
}
