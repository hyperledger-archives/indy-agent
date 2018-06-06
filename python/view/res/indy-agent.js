(function(){

    // Message Router {{{
    var msg_router = {
        routes: [],
        route:
            function(msg) {
                if (msg.type in this.routes) {
                    this.routes[msg.type](msg.data);
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

    function edge_connect(event) {
        socket.send(JSON.stringify(
            {
                "type": "EDGE_CONNECT",
                "did": null,
                "data": null
            }
        ));
    }

    function send_request(event) {
        send_req_msg = {
            type: "SEND_REQ",
            did: null,
            data: {
                endpoint: document.getElementById('send_endpoint').value
            }
        }
        socket.send(JSON.stringify(send_req_msg));
        event.stopPropagation();
    }

    function agent_init(event) {
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

    function recv_state(state) {
        document.getElementById('agent_name').value = state.agent_name;
        document.getElementById('agent_name_header').value = state.agent_name;
    }
    msg_router.register('AGENT_STATE', recv_state);

    document.getElementById('send_request').addEventListener(
        "click",
        send_request
    );

    document.getElementById('agent_init').addEventListener(
        "click",
        agent_init
    );


    // Create WebSocket connection.
    const socket = new WebSocket('ws://localhost:8080/ws');

    // Connection opened
    socket.addEventListener('open', edge_connect);

    // Listen for messages
    socket.addEventListener('message', function (event) {
        console.log('Routing: ' + event.data);
        msg = JSON.parse(event.data);
        msg_router.route(msg);
    });

})();
