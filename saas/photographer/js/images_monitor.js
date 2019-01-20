/**
 * Images monitor.
 *
 * The images monitor checks wether all images on the
 * current page have loaded.
 *
 * The number of images on the page may change, to ensure
 * that all images have been loaded window.__selenium_was_equal
 * should be greater than 2-5 for atleast a second or two.
 */

/**
 * How many times all images on the page have been loaded.
 *
 * @type {Number}
 */
window.__selenium_was_equal = 0;

/**
 * The number of images found on the page.
 *
 * @type {Number}
 */
window.__selenium_images = 0;

setInterval(function() {
    var imgs = document.images;

    if (imgs.length !== window.__selenium_images) {
        window.__selenium_images = imgs.length;
        window.__selenium_was_equal = 0;
    }

    var loaded = 0;
    for (var i = imgs.length - 1; i >= 0; i--) {
        if (imgs[i].complete) {
            loaded++;
        }
    }

    if (loaded === imgs.length) {
        window.__selenium_was_equal++;
    }
}, 200);
