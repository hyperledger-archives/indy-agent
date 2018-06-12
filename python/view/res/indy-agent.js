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

    const connection_template = Handlebars.compile(document.getElementById('connection-template').innerHTML);

    function ui_connect(socket, msg) {
        socket.send(JSON.stringify(
            {
                "type": "UI_CONNECT",
                "did": null,
                "data": null
            }
        ));
    }

    function send_request(socket, event) {
        send_req_msg = {
            type: "SEND_REQ",
            did: null,
            data: {
                name: document.getElementById('send_name').value,
                endpoint: document.getElementById('send_endpoint').value
            }
        }
        socket.send(JSON.stringify(send_req_msg));
        event.stopPropagation();
    }

    function agent_init(socket, event) {
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
        event.stopPropagation();
    }

    function conn_req_recv(socket, msg) {
        document.getElementById('connections').innerHTML += '<li>' + msg.owner + '</li>';
    }

    function recv_state(socket, state) {
        document.getElementById('agent_name').value = state.agent_name;
        document.getElementById('agent_name_header').innerHTML = state.agent_name;
        conn_wrapper = document.getElementById('connections-wrapper');
        console.log(state.connections);
        console.log(connection_template);
        context = {'connections': state.connections};
        console.log(context);
        content = connection_template(context);
        console.log(content);
        conn_wrapper.innerHTML = content;

    }

    msg_router.register('AGENT_STATE', recv_state);
    msg_router.register('CONN_REQ_RECV', conn_req_recv);

    // Create WebSocket connection.
    const socket = new WebSocket('ws://localhost:8080/ws');

    // Connection opened
    socket.addEventListener('open', function(event) {
        ui_connect(socket, event);
    });

    // Listen for messages
    socket.addEventListener('message', function (event) {
        console.log('Routing: ' + event.data);
        msg = JSON.parse(event.data);
        msg_router.route(socket, msg);
    });

    document.getElementById('send_request').addEventListener(
        "click",
        function (event) {
            send_request(socket, event);
        }
    );

    document.getElementById('agent_init').addEventListener(
        "click",
        function (event) {
            agent_init(socket, event);
        }
    );

})();
