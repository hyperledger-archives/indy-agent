// Extension Communication {{{
function caller(message, sender, sendResponse) {
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
        case "saveAgentKey":
            saveAgentKey(message.key);
            break;
        case "pack":
            keys = getKeys();
            agent_key = getAgentKey();
            ret_val = indy.pack_message(message.message, [agent_key], keys);
            break;
        case "unpack":
            keys = getKeys();
            ret_val = indy.unpack_message(message.message, keys);
            break;
        default:
            console.error("Unrecognized caller data: " + JSON.stringify(message));
            break;
    }
    if (ret_val) {
        sendResponse(ret_val);
    }
}
browser.runtime.onMessage.addListener(caller);
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
function saveAgentKey(key) {
    localStorage.setItem('agent-key', key);
}
function getAgentKey() {
    let key = localStorage.getItem('agent-key');
    if (!key) {
        return null;
    }
    return Base58.decode(key);
}
// }}}
