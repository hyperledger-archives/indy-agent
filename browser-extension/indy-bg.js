
// Extension Communication to content script {{{
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
        case "pack":
            ret_val = pack_message(message);
            break;
        case "unpack":
            ret_val = unpack_message(message);
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


// crypto sandbox communication {{{
window.onload = function(){
    crypto_frame = document.getElementById('cryptoframe').contentWindow;
};

let pending_promises = {};
async function crypto_call(msg){
    let envelope = {
        'tag': Date.now(), //used to correlate responses
        'msg': msg
    };
    let response_promise = new Promise((resolve, reject) => {
        pending_promises[envelope.tag] = resolve;
        setTimeout(() => reject(false), 1000); //fail if not back in 1 second
    });


    crypto_frame.postMessage(envelope, '*');

    let crypto_response = await response_promise;
    return crypto_response;
}
window.addEventListener('message', function(event) {
    console.log("message from crypto_sandbox", event);
    let promise_tag = event.data.tag;
    let pending_promise = pending_promises[promise_tag];
    pending_promise(event.data.response);
});
// }}}


// Key Management {{{
function getKeys() {
    let ser_keys = localStorage.getItem('keys')
    if (!ser_keys) {
        return null;
    }
    return deserializeKeys(ser_keys);
}
async function generateKeys() {
    if (!localStorage.getItem('keys')) {
        //keys = sodium.crypto_sign_keypair();
        keys = await crypto_call({"method":"crypto_sign_keypair"});
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
async function pack_message(message){

    keys = getKeys();
    to_key = Base58.decode(message.to_key);
    //ret_val = indy.pack_message(message.message, [to_key], keys);
    packed = await crypto_call({"method":"pack_message", "message":message.message, "to_keys":[to_key], "keys":keys});
    return packed;
}
async function unpack_message(message){
    keys = getKeys();
    //ret_val = indy.unpack_message(message.message, keys);
    unpacked = await crypto_call({"method":"unpack_message", "message":message.message, "keys":keys});
    return unpacked;
}
// }}}
