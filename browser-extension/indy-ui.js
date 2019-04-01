function generateKeys() {
    browser.runtime.sendMessage({
        method: "generateKeys"
    }).then(function(){
        displayPublicKey();
    });
}

function removeKeys() {
    browser.runtime.sendMessage({
        method: "removeKeys"
    }).then(function(){
        displayPublicKey();
    });
}

function displayPublicKey() {
    browser.runtime.sendMessage({
        method: "getPublicKey"
    }).then(function(response) {
        document.getElementById('public-key').value = response || "-- no key --";
    });
}

function copyPublicKey() {
    document.getElementById('public-key').select();
    document.execCommand('copy');
}

displayPublicKey();
document.getElementById('generate-keys').addEventListener('click', generateKeys);
document.getElementById('remove-keys').addEventListener('click', removeKeys);
document.getElementById('copy-public-key').addEventListener('click', copyPublicKey);
