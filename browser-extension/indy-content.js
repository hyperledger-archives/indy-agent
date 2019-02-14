let port = browser.runtime.connect({name: 'connector'});

window.addEventListener("message", function(event) {
    if (event.source == window &&
        event.data &&
        event.data.direction == "from-page-script") {
        call_to_background(event.data.call);
    }
});

function call_to_background(call_data) {
    res = browser.runtime.sendMessage(call_data);
    res.then(function(response) {
        window.postMessage(
            {
                direction: "from-content-script",
                method: call_data.method
                response: response,
            }
        )
    })
}
