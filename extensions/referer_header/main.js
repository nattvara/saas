/**
 * This will modify all requests to have a Referer header
 * with the value "https://google.com".
 *
 * The reason for this is some website uses paywalls but allows
 * incomming traffic from google.com to bypass those paywalls.
 */

rewriteRequest = (e) => {
    e.requestHeaders.push({
        name: 'Referer',
        value: 'https://google.com'
    })
    return {
        requestHeaders: e.requestHeaders
    };
}

browser.webRequest.onBeforeSendHeaders.addListener(
    rewriteRequest,
    {
        urls: ['*://*/*']
    },
    [
        'blocking',
        'requestHeaders'
    ]
);
