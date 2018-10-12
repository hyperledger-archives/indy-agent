(function(){

    const TOKEN = document.getElementById("ui_token").innerText;

    var sendInviteButton = document.getElementById("btn_send_invite");

    connectionsTable = document.getElementById("conns-new");

    const MESSAGE_TYPES = {
        CONN_BASE: "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/",
        UI_BASE: "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/sovrin.org/ui/1.0/"};

    const UI_MESSAGE = {
        STATE: MESSAGE_TYPES.UI_BASE + "state",
        STATE_REQUEST: MESSAGE_TYPES.UI_BASE + "state_request",
        INITIALIZE: MESSAGE_TYPES.UI_BASE + "initialize",

        SEND_INVITE: MESSAGE_TYPES.UI_BASE + "send_invite",
        INVITE_SENT: MESSAGE_TYPES.UI_BASE + "invite_sent",
        INVITE_RECEIVED: MESSAGE_TYPES.UI_BASE + "invite_received",

        SEND_REQUEST: MESSAGE_TYPES.UI_BASE + "send_request",
        REQUEST_SENT: MESSAGE_TYPES.UI_BASE + "request_sent",

        SEND_RESPONSE: MESSAGE_TYPES.UI_BASE + "send_response",
        RESPONSE_SENT: MESSAGE_TYPES.UI_BASE + "response_sent",
    };

    const CONN_MESSAGE = {
        REQUEST_RECEIVED:MESSAGE_TYPES.CONN_BASE + "request",
        RESPONSE_RECEIVED: MESSAGE_TYPES.CONN_BASE + "response"
    };

    // Message Router {{{
    var msg_router = {
        routes: [],
        route:
            function(socket, msg) {
                if (msg.type in this.routes) {
                    this.routes[msg.type](socket, msg);
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
                    type: UI_MESSAGE.STATE_REQUEST,
                    id: TOKEN,
                    content: null
                }
            ));
        },
        update:
        function (socket, msg) {
            state = msg.content;
            if (state.initialized === false) {
                showTab('login');
            } else {
                document.getElementById('agent_name').value = state.agent_name;
                document.getElementById('agent_name_header').innerHTML = "Agent's name: " + state.agent_name;
                showTab('relationships');
            }
        },
        inititialize:
        function (socket) {
            init_message = {
                type: UI_MESSAGE.INITIALIZE,
                id: TOKEN,
                content: {
                    name: document.getElementById('agent_name').value,
                    passphrase: document.getElementById('passphrase').value
                }
            };
            socket.send(JSON.stringify(init_message));
        },
    };
    // }}}


    // Connections {{{
    var connections = {
        send_invite:
        function (socket) {
            msg = {
                type: UI_MESSAGE.SEND_INVITE,
                id: TOKEN,
                content: {
                    name: document.getElementById('send_name').value,
                    endpoint: document.getElementById('send_endpoint').value
                }
            };
            socket.send(JSON.stringify(msg));

        },

        invite_sent:
        function (socket, msg) {
            displayConnection(msg.content.name, [], 'Invite sent');
        },

        invite_received:
        function (socket, msg) {
            document.getElementById("history_body").innerText = getTodayDate() + ": " + displayObject(msg.content.history);

            displayConnection(msg.content.name, [['Send Request', connections.send_request, socket, msg]], 'Invite received');
        },

        send_request:
        function (socket, prevMsg) {
            msg = {
                type: UI_MESSAGE.SEND_REQUEST,
                id: TOKEN,
                content: {
                        name: prevMsg.content.name,
                        endpoint: prevMsg.content.endpoint.url,
                        key: prevMsg.content.endpoint.verkey,
                }
            };
            socket.send(JSON.stringify(msg));

        },

        request_sent:
        function (socket, msg) {
            removeRow(msg.content.name);
            displayConnection(msg.content.name, [], 'Request sent');
        },

        request_received:
        function (socket, msg) {
            document.getElementById("history_body").innerText = getTodayDate() + ": " + displayObject(msg.content.history);
            removeRow(msg.content.name);
            displayConnection(msg.content.name, [['Send response', connections.send_response, socket, msg]], 'Request received');
        },

        send_response:
        function (socket, prevMsg) {
            msg = {
                type: UI_MESSAGE.SEND_RESPONSE,
                id: TOKEN,
                content: {
                        name: prevMsg.content.name,
                        endpoint_key: prevMsg.content.endpoint_key,
                        endpoint_uri: prevMsg.content.endpoint_uri,
                        endpoint_did: prevMsg.content.endpoint_did
                }
            };
            socket.send(JSON.stringify(msg));
        },

        response_sent:
        function (socket, msg) {
            removeRow(msg.content.name);
            displayConnection(msg.content.name, [], 'Response sent');
        },

        response_received:
        function (socket, msg) {
            document.getElementById("history_body").innerText += getTodayDate() + ": " + displayObject(msg.content.history);
            removeRow(msg.content.name);
            displayConnection(msg.content.name, [], 'Response received');
        },

    };
    // }}}

    // Message Routes {{{
    msg_router.register(UI_MESSAGE.STATE, ui_agent.update);
    msg_router.register(UI_MESSAGE.INVITE_SENT, connections.invite_sent);
    msg_router.register(UI_MESSAGE.INVITE_RECEIVED, connections.invite_received);
    msg_router.register(UI_MESSAGE.REQUEST_SENT, connections.request_sent);
    msg_router.register(CONN_MESSAGE.RESPONSE_RECEIVED, connections.response_received);
    msg_router.register(CONN_MESSAGE.REQUEST_RECEIVED, connections.request_received);
    msg_router.register(UI_MESSAGE.RESPONSE_SENT, connections.response_sent);

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
    document.getElementById('send_offer').addEventListener(
        "click",
        function (event) { connections.send_invite(socket); }
    );

    document.getElementById('agent_init').addEventListener(
        "click",
        function (event) {
            ui_agent.inititialize(socket);
            sendInviteButton.style.display = "block";
        }
    );

    function displayConnection(connName, actions, status) {
        let row = connectionsTable.insertRow();
        row.id = connName + "_row";
        let cell1 = row.insertCell();
        let cell2 = row.insertCell();
        let cell3 = row.insertCell();
        let cell4 = row.insertCell();
        let cell5 = row.insertCell();

        let history_btn = document.createElement("button");
        history_btn.id = connName + "_history";
        history_btn.type = "button";
        history_btn.className = "btn btn-info";
        history_btn.textContent = "View";
        history_btn.setAttribute('data-toggle', 'modal');
        history_btn.setAttribute('data-target', '#exampleModal');

        actions.forEach(function (item, i, actions) {
            let butn = document.createElement("button");
            butn.id = connName + "_" + item[0];
            butn.type = "button";
            butn.className = "btn btn-warning   ";
            butn.textContent = item[0];
            butn.addEventListener(
                "click",
                function (event) {
                     item[1](item[2], item[3]);
                }
            );
            cell5.appendChild(butn);

        });

        cell1.innerHTML = "#";
        cell2.innerHTML = connName;
        cell3.innerHTML = status;
        cell4.appendChild(history_btn);
    }

    // }}}

})();
