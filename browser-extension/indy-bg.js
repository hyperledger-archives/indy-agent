// Extension UI Communication {{{
function ui_message_listener(message, sender, sendResponse) {
    console.log(sender);
    let ret_val = null;
    switch (message.method) {
        case "generateKeys":
            generateKeys();
            break;
        case "removeKeys":
            removeKeys();
            break;
        case "getPublicKey":
            ret_val = getPublicKey();
            break;
        default:
            console.error("Unrecognized UI message: " + JSON.stringify(message));
            break;
    }
    if (ret_val) {
        sendResponse({ret: ret_val});
    }
}
browser.runtime.onMessage.addListener(ui_message_listener);
// }}}

// Key Management {{{
function getKeys() {
    let ser_keys = localStorage.getItem('keys')
    if (!ser_keys) {
        return null;
    }
    return deserializeKeys(ser_keys);
}
function generateKeys() {
    if (!localStorage.getItem('keys')) {
        keys = sodium.crypto_sign_keypair();
        localStorage.setItem('keys', serializeKeys(keys));
    }
}

function removeKeys() {
    localStorage.removeItem('keys');
}
function serializeKeys(keys) {
    keys.publicKey = Base58.encode(keys.publicKey);
    keys.privateKey = Base58.encode(keys.privateKey);
    return JSON.stringify(keys);
}
function deserializeKeys(serialized_keys) {
    let keys = JSON.parse(serialized_keys);
    keys.publicKey = Base58.decode(keys.publicKey);
    keys.privateKey = Base58.decode(keys.privateKey);
    return keys;
}
function getPublicKey() {
    let keys = JSON.parse(localStorage.getItem('keys'));
    if (!keys) {
        return "";
    }
    return keys.publicKey;
}
// }}}
