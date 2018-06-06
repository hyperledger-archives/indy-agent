(function(){

    // Create WebSocket connection.
    const socket = new WebSocket('ws://localhost:8080/ws');

    // Connection opened
    socket.addEventListener('open', function (event) {
        socket.send('Hello Server!');
    });

    // Listen for messages
    socket.addEventListener('message', function (event) {
        console.log('Message from server ', event.data);
    });

    document.getElementById('send_request').addEventListener(
        "click",
        function (event) {
            socket.send('{"type": "SEND_REQ", "did": null, "data": {"endpoint": "http://localhost:8080/indy"}}');
            event.stopPropagation();
        }
    );

    document.getElementById('agent_init').addEventListener(
        "click",
        function (event) {
            init_message = {
                "type": "AGENT_INIT",
                "did": null,
                "data": {
                    "name": document.getElementById('agent_name').value,
                    "endpoint": document.getElementById('agent_endpoint').value
                }
            };
            socket.send(JSON.stringify(init_message));
            document.getElementById('id01').style.display = 'none';
            event.stopPropagation();
        }
    );

})();
