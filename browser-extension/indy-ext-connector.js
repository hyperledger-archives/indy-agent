let port = browser.runtime.connect({name: 'connector'});

window.addEventListener("message", function(event) {
  if (event.source == window &&
      event.data &&
      event.data.direction == "from-page-script") {

  }
});
