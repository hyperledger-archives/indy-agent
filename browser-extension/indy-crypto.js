
// background communication {{{

function caller(m, sendResponse) {
    let ret_val = null;
    switch (m.method) {
        case "crypto_sign_keypair":
            ret_val = sodium.crypto_sign_keypair();
            break;
        case "pack_message":
            ret_val = indy.pack_message(m.message, m.to_keys, m.keys);
            break;
        case "unpack_message":
            ret_val = indy.unpack_message(m.message, m.keys);
            break;
        default:
            console.error("Unrecognized caller data: " + JSON.stringify(m));
            break;
    }
    if (ret_val) {
        sendResponse(ret_val);
    }
}
window.addEventListener('message', function(event) {
    console.log("message from background_page", event);
    let promise_tag = event.data.tag;

    caller(event.data.msg, function(response){
        let envelope = {
            'tag': promise_tag,
            'response': response
        };
        event.source.postMessage(envelope, "*");
    });
});
// }}}

