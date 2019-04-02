    const MESSAGE_TYPES = {
        CONN_BASE: "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/",
        ADMIN_CONNECTIONS_BASE: "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin_connections/1.0/",
        ADMIN_BASE: "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin/1.0/",
        ADMIN_WALLETCONNECTION_BASE: "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin_walletconnection/1.0/",
        ADMIN_BASICMESSAGE_BASE: "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin_basicmessage/1.0/",
        ADMIN_TRUSTPING_BASE: "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin_trustping/1.0/"
    };

    const ADMIN = {
        STATE: MESSAGE_TYPES.ADMIN_BASE + "state",
        STATE_REQUEST: MESSAGE_TYPES.ADMIN_BASE + "state_request"
    };

    const ADMIN_WALLETCONNECTION = {
        CONNECT: MESSAGE_TYPES.ADMIN_WALLETCONNECTION_BASE + 'connect',
        DISCONNECT: MESSAGE_TYPES.ADMIN_WALLETCONNECTION_BASE + 'disconnect',
        USER_ERROR: MESSAGE_TYPES.ADMIN_WALLETCONNECTION_BASE + 'user_error'
    };

    const ADMIN_CONNECTION = {
        CONNECTION_LIST: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "connection_list",
        CONNECTION_LIST_REQUEST: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "connection_list_request",

        GENERATE_INVITE: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "generate_invite",
        INVITE_GENERATED: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "invite_generated",
        INVITE_RECEIVED: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "invite_received",
        RECEIVE_INVITE: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "receive_invite",

        SEND_REQUEST: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "send_request",
        REQUEST_SENT: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "request_sent",
        REQUEST_RECEIVED:MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "request_received",

        SEND_RESPONSE: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "send_response",
        RESPONSE_SENT: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "response_sent",
        RESPONSE_RECEIVED: MESSAGE_TYPES.ADMIN_CONNECTIONS_BASE + "response_received"
    };

    const ADMIN_BASICMESSAGE = {
        SEND_MESSAGE: MESSAGE_TYPES.ADMIN_BASICMESSAGE_BASE + "send_message",
        MESSAGE_SENT: MESSAGE_TYPES.ADMIN_BASICMESSAGE_BASE + "message_sent",
        MESSAGE_RECEIVED: MESSAGE_TYPES.ADMIN_BASICMESSAGE_BASE + "message_received",
        GET_MESSAGES: MESSAGE_TYPES.ADMIN_BASICMESSAGE_BASE + "get_messages",
        MESSAGES: MESSAGE_TYPES.ADMIN_BASICMESSAGE_BASE + "messages"
    };

    const ADMIN_TRUSTPING = {
        SEND_TRUSTPING: MESSAGE_TYPES.ADMIN_TRUSTPING_BASE + "send_trustping",
        TRUSTPING_SENT: MESSAGE_TYPES.ADMIN_TRUSTPING_BASE + "trustping_sent",
        TRUSTPING_RECEIVED: MESSAGE_TYPES.ADMIN_TRUSTPING_BASE + "trustping_received",
        TRUSTPING_RESPONSE_RECEIVED: MESSAGE_TYPES.ADMIN_TRUSTPING_BASE + "trustping_response_received"
    };

    window.indy_connector.ping();
    const agent_admin_key = document.head.querySelector("[name=agent_admin_key][content]").content;

    // Create WebSocket connection.
    const socket = new WebSocket('ws://' + window.location.hostname + ':' + window.location.port + '/ws');

    // Connection opened
    socket.addEventListener('open', function(event) {
        ui_agent.connect();
    });

    // Listen for messages
    socket.addEventListener('message', function (event) {
        if (indy_connector.extension_exists) {
            console.log("attempting to unpack");
            indy_connector.unpack_message(event.data);
        } else {
            console.log('Routing: ' + event.data);
            msg = JSON.parse(event.data);
            msg_router.route(msg);
            thread_router.route(msg);
        }
    });


    function sendMessage(msg, thread_cb){
        //decorate message as necessary
        msg.id = (new Date()).getTime(); // ms since epoch

        // register thread callback
        if(typeof thread_cb !== "undefined") {
            thread_router.register(msg.id, thread_cb);
        }

        // TODO: Encode properly when wire protocol is finished
        if (indy_connector.extension_exists) {
            console.log("Packing message: ", msg);
            indy_connector.pack_message(JSON.stringify(msg), agent_admin_key);
        } else {
            console.log("sending message", msg);
            socket.send(JSON.stringify(msg));
        }
    }

    indy_connector.register_pack_cb(function(message) {
        console.log("sending message", message);
        socket.send(message);
    });

    indy_connector.register_unpack_cb(function(result) {
        console.log('Routing: ', result.message);
        msg = JSON.parse(result.message);
        msg_router.route(msg);
        thread_router.route(msg);
    });

    // Message Router {{{
    var msg_router = {
        routes: [],
        route:
            function(msg) {
                if (msg['@type'] in this.routes) {
                    this.routes[msg['@type']](msg);
                } else {
                    console.log('Message from server without registered route: ' + JSON.stringify(msg));
                }
            },
        register:
            function(msg_type, fn) {
                this.routes[msg_type] = fn
            }
    };
    // }}}

    // Limitation: this thread router only allows one cb per thread.
    var thread_router = {
        default_thread_expiration: 1000 * 60 * 5, // in milliseconds
        thread_handlers: {},
        route: function(msg){
            if(!("thread" in msg)){
                return; //no thread, no callbacks possible
            }
            thid = msg["thread"]["thid"];
            if(thid in this.thread_handlers){
                this.thread_handlers[thid]["handler"](msg);
            }
        },
        register: function(thread_id, thread_cb){
            this.thread_handlers[thread_id] = {
                "handler": thread_cb,
                "expires": (new Date()).getTime() + this.default_thread_expiration
            };
        },
        clean_routes: function(){
            // TODO: look through handlers and clean out expired ones.
        }
    };

    // this is shared data among all the vue instances for simplicity.
    var ui_data = {
        wallet_connect_error: '',
        agent_name: '',
        passphrase: '',
        current_tab: 'login',
        generated_invite: {
            invite: ""
        },
        receive_invite_info: {
            label: "",
            invite: ""
        },
        connections: [],
        pairwise_connections:[],
        connection: {},
        new_basicmessage: "",
        basicmessage_list: [],
        history_view: []
    };

    Vue.use(vueMoment);

    var ui_credentials = new Vue({
        el: '#credentials',
        data: ui_data,
        computed: {
            tab_active: function(){
                return this.current_tab === "credentials";
            }
        }
    });

    var ui_relationships = new Vue({
        el: '#relationships',
        data: ui_data,
        computed: {
            tab_active: function(){
                return this.current_tab === "relationships";
            }
        },
        methods: {
            generate_invite: function () {
                msg = {
                    '@type': ADMIN_CONNECTION.GENERATE_INVITE,
                };
                sendMessage(msg);
            },
            invite_generated: function (msg) {
                this.generated_invite.invite = msg.invite;
                $('#generated_invite_modal').modal('show');
            },
            copy_invite: function() {
                document.getElementById('invite').select();
                console.log(document.execCommand('copy'));
            },
            invite_received: function (msg) {
                this.connections.push({
                    label: msg.label,
                    connection_key: msg.connection_key,
                    endpoint: msg.endpoint,
                    status: msg.status  ,
                    history: history_log_format(msg.history)
                });
            },

            receive_invite: function (c) {
                msg = {
                    '@type': ADMIN_CONNECTION.RECEIVE_INVITE,
                    label: this.receive_invite_info.label,
                    invite: this.receive_invite_info.invite
                };
                sendMessage(msg);
            },
            send_request: function (c) {
                msg = {
                    '@type': ADMIN_CONNECTION.SEND_REQUEST,
                    connection_key: c.connection_key
                };
                sendMessage(msg);
            },
            request_sent: function (msg) {
                var c = this.get_connection_by_key(msg.connection_key);
                c.status = msg.status;
            },
            request_received: function (msg) {
                this.connections.push({
                    label: msg.label,
                    did: msg.did,
                    status: msg.status,
                    connection_key: msg.connection_key,
                    history: history_log_format(msg.history)
                })
            },
            send_response: function (c) {
                msg = {
                    '@type': ADMIN_CONNECTION.SEND_RESPONSE,
                    'did': c.did,
                };
                sendMessage(msg);
            },
            response_sent: function (msg) {
                // request a state update to see the new pairwise connection
                // this.connections will be emptied at the same time
                sendMessage({'@type': ADMIN.STATE_REQUEST});
            },
            response_received: function (msg) {
                // request a state update to see the new pairwise connection
                // this.connections will be emptied at the same time
                sendMessage({'@type': ADMIN.STATE_REQUEST});
            },
            message_sent: function (msg) {
                if(msg.with == this.connection.their_did){
                    //connection view currently open
                    sendMessage({
                        '@type': ADMIN_BASICMESSAGE.GET_MESSAGES,
                        with: msg.with
                    });
                } else {
                    //connection not currently open. set unread flag on connection details?
                }
            },
            message_received: function (msg) {
                if(msg.with == this.connection.their_did){
                    //connection view currently open
                    sendMessage({
                        '@type': ADMIN_BASICMESSAGE.GET_MESSAGES,
                        with: msg.with
                    });
                } else {
                    //connection not currently open. set unread flag on connection details?
                }
            },
            messages: function(msg){
                this.basicmessage_list = msg.messages;
            },
            display_history: function(connection){
                this.history_view = connection.history;
                console.log(this.history_view);
                $('#historyModal').modal({});
            },
            get_connection_by_key: function(connection_key){
               return this.connections.find(function(x){return x.connection_key === connection_key;});
            },
            show_connection: function(c){
                Vue.set(c, 'trustping_state', ""); // set here to allow vue to bind.
                this.connection = c;
                ui_connection.load();
                this.current_tab = "connection";
            }
        }
    });

    // Single Connection
    var ui_connection = new Vue({
        el: "#connection",
        data: ui_data,
        computed: {
            tab_active: function(){
                return this.current_tab === "connection";
            }
        },
        methods: {
            send_message: function(){
                msg = {
                    '@type': ADMIN_BASICMESSAGE.SEND_MESSAGE,
                    to: this.connection.their_did,
                    message: this.new_basicmessage
                };
                sendMessage(msg);
                this.new_basicmessage = "";
            },
            load: function(){
                sendMessage({
                    '@type': ADMIN_BASICMESSAGE.GET_MESSAGES,
                    with: this.connection.their_did
                });
            },
            send_trustping: function(){
                msg = {
                    '@type': ADMIN_TRUSTPING.SEND_TRUSTPING,
                    to: this.connection.their_did,
                    from: this.connection.did,
                    message: "Send trustping"
                };
                Vue.set(this.connection, 'trustping_state', "Sending...");
                sendMessage(msg);
            },
            trustping_sent: function(msg){
                console.log("sent", msg);
                Vue.set(this.connection, 'trustping_state', "Sent.");
            },
            trustping_received: function (msg) {
                if(msg.from == this.connection.their_did){
                    //connection view currently open
                    Vue.set(this.connection, 'trustping_state', "Received Ping.");
                } else {
                    //connection not currently open. set unread flag on connection details?
                }
            },
            trustping_response_received: function (msg) {
                if(msg.from == this.connection.their_did){
                    //connection view currently open
                    Vue.set(this.connection, 'trustping_state', "Received Response.");
                } else {
                    //connection not currently open. set unread flag on connection details?
                }
            },
        }
    });

    var ui_title = new Vue({
        el: 'title',
        data: ui_data,
    });

    var ui_header = new Vue({
        el: '#header',
        data: ui_data,
        computed:{

        },
        methods: {
            set_tab: function(t){
                this.current_tab = t;

            }
        }
    });

    // UI Agent {{{
    var ui_agent = new Vue({
        el: '#login',
        data: ui_data,
        computed: {
            tab_active: function(){
                return this.current_tab === "login";
            }
        },
        methods: {
            walletconnnect: function () {
                this.wallet_connect_error = ""; // clear any previous error
                //var v_this = this;
                sendMessage({
                    '@type': ADMIN_WALLETCONNECTION.CONNECT,
                    name: this.agent_name,
                    passphrase: this.passphrase
                }, function(msg){
                    //thread callback
                    console.log("received thread response", msg);
                    if(msg['@type'] === ADMIN_WALLETCONNECTION.USER_ERROR){
                        this.wallet_connect_error = msg.message;
                    }
                }.bind(this));
            },
            connect: function(){
                sendMessage(
                    {
                        '@type': ADMIN.STATE_REQUEST,
                        content: null
                    }
                );
            },
            update: function (msg) {
                state = msg.content;
                if (state.initialized === false) {
                    this.current_tab = 'login';
                } else {
                    this.agent_name = state.agent_name;
                    this.current_tab = 'relationships';
                    //load invitations

                    console.log('invitations', state.invitations);
                    // Load pending connections while beautifying history messages
                    this.connections = []
                    state.invitations.forEach((i) => {
                        i.history = history_log_format(i.history)
                        this.connections.push(i);
                    });
                    // Load pairwise connections
                    this.pairwise_connections = state['pairwise_connections'];
                }
            }
        }
    });


    // }}}

    // Message Routes {{{
    msg_router.register(ADMIN.STATE, ui_agent.update);
    msg_router.register(ADMIN_CONNECTION.INVITE_GENERATED, ui_relationships.invite_generated);
    msg_router.register(ADMIN_CONNECTION.INVITE_RECEIVED, ui_relationships.invite_received);
    msg_router.register(ADMIN_CONNECTION.REQUEST_SENT, ui_relationships.request_sent);
    msg_router.register(ADMIN_CONNECTION.RESPONSE_SENT, ui_relationships.response_sent);
    msg_router.register(ADMIN_BASICMESSAGE.MESSAGE_SENT, ui_relationships.message_sent);
    msg_router.register(ADMIN_CONNECTION.RESPONSE_RECEIVED, ui_relationships.response_received);
    msg_router.register(ADMIN_CONNECTION.REQUEST_RECEIVED, ui_relationships.request_received);
    msg_router.register(ADMIN_BASICMESSAGE.MESSAGE_RECEIVED, ui_relationships.message_received);
    msg_router.register(ADMIN_BASICMESSAGE.MESSAGES, ui_relationships.messages);
    msg_router.register(ADMIN_TRUSTPING.TRUSTPING_SENT, ui_connection.trustping_sent);
    msg_router.register(ADMIN_TRUSTPING.TRUSTPING_RECEIVED, ui_connection.trustping_received);
    msg_router.register(ADMIN_TRUSTPING.TRUSTPING_RESPONSE_RECEIVED, ui_connection.trustping_response_received);

    // }}}

