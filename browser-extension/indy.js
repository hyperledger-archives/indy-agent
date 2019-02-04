"use strict";

console.log("Indy BG");

function handleMessage(request, sender, sendResponse) {
    console.log(request, sender, sendResponse);
    sendResponse({response: "asdf"});
}

browser.runtime.onMessage.addListener(handleMessage);
