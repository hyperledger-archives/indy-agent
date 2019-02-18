window.indy_connector = {};
window.indy_connector.extension_exists = false;

(function() {

    register_cb('pong', pong);

    function pong() {
        window.indy_connector.extension_exists = true;
    }

    function ping() {
        window.postMessage(
            {
                direction: "from-page-script",
                method: "ping"
            },
            "*"
        );
    }

    function pack_message(message, to_key) {
        window.postMessage(
            {
                direction: "from-page-script",
                method: 'pack',
                message: message,
                to_key: to_key
            },
            "*"
        );
    }

    function unpack_message(message) {
        window.postMessage(
            {
                direction: "from-page-script",
                method: 'unpack',
                message: message
            },
            "*"
        );
    }

    function register_cb(method, cb) {
        window.addEventListener("message", function(event) {
            if (event.source == window &&
                event.data &&
                event.data.direction == "from-content-script" &&
                event.data.method == method) {

                cb(event.data.response);
            }
        })
    }

    function register_pack_cb(cb) {
        register_cb('pack', cb);
    }
    function register_unpack_cb(cb) {
        register_cb('unpack', cb);
    }

    indy_connector.pack_message = pack_message;
    indy_connector.unpack_message = unpack_message;
    indy_connector.register_pack_cb = register_pack_cb;
    indy_connector.register_unpack_cb = register_unpack_cb;
    indy_connector.ping = ping;
}).call(this);
