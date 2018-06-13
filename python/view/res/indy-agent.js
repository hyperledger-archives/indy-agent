(function(){

    // Message Router {{{
    var msg_router = {
        routes: [],
        route:
            function(socket, msg) {
                if (msg.type in this.routes) {
                    this.routes[msg.type](socket, msg.data);
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

    // UI Agent {{{
    var ui_agent = {
        connect:
        function (socket) {
            socket.send(JSON.stringify(
                {
                    "type": "UI_CONNECT",
                    "did": null,
                    "data": null
                }
            ));
        },
        update:
        function (socket, state) {
            document.getElementById('agent_name').value = state.agent_name;
            document.getElementById('agent_name_header').innerHTML = state.agent_name;
            conn_wrapper = document.getElementById('connections-wrapper');
            context = {'connections': state.connections};
            content = connections_template(context);
            conn_wrapper.innerHTML = content;
        },
        inititialize:
        function (socket) {
            init_message = {
                type: "AGENT_INIT",
                did: null,
                data: {
                    name: document.getElementById('agent_name').value,
                    endpoint: document.getElementById('agent_endpoint').value
                }
            };
            socket.send(JSON.stringify(init_message));
            document.getElementById('id01').style.display = 'none';
        },
    };
    // }}}

    // Connections {{{
    var connections = {
        send_request:
        function (socket) {
            send_req_msg = {
                type: "SEND_REQ",
                did: null,
                data: {
                    name: document.getElementById('send_name').value,
                    endpoint: document.getElementById('send_endpoint').value
                }
            }
            socket.send(JSON.stringify(send_req_msg));
        },
        connection_request_sent:
        function (socket, msg) {
            context = {name: msg.name, status: msg.status};
            document.getElementById('connections-wrapper').innerHTML += connection_template(context);
        },
        connection_request_recieved:
        function (socket, msg) {
            context = {name: msg.owner, status: msg.status};
            document.getElementById('connections-wrapper').innerHTML += connection_template(context);
        }
    };
    // }}}

    // Templates {{{

    const connections_template = Handlebars.compile(document.getElementById('connections-template').innerHTML);
    const connection_template = Handlebars.compile(document.getElementById('connection-template').innerHTML);

    // }}}

    // Message Routes {{{
    msg_router.register('AGENT_STATE', ui_agent.update);
    msg_router.register('CONN_REQ_SENT', connections.connection_request_sent);
    msg_router.register('CONN_REQ_RECV', connections.connection_request_recieved);

    // }}}

    // Create WebSocket connection.
    const socket = new WebSocket('ws://' + window.location.hostname + ':' + window.location.port + '/ws');

    // Connection opened
    socket.addEventListener('open', function(event) {
        ui_agent.connect(socket);
    });

    // Listen for messages
    socket.addEventListener('message', function (event) {
        console.log('Routing: ' + event.data);
        msg = JSON.parse(event.data);
        msg_router.route(socket, msg);
    });

    // DOM Event Listeners {{{
    // Need reference to socket so must be after socket creation
    document.getElementById('send_request').addEventListener(
        "click",
        function (event) { connections.send_request(socket); }
    );

    document.getElementById('agent_init').addEventListener(
        "click",
        function (event) { ui_agent.inititialize(socket); }
    );

    // }}}

})();
