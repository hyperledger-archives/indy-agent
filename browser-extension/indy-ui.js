var browser = (browser ? browser : chrome);

function generateKeys() {
    browser.runtime.sendMessage({
        method: "generateKeys"
    });
    getPublicKey();
}

function removeKeys() {
    browser.runtime.sendMessage({
        method: "removeKeys"
    });
    document.getElementById('public-key').value = "";
}

function getPublicKey() {
    let res = browser.runtime.sendMessage({
        method: "getPublicKey"
    });
    res.then(function(response) {
        document.getElementById('public-key').value = response;
    })
}

function copyPublicKey() {
    document.getElementById('public-key').select();
    document.execCommand('copy');
}

getPublicKey();
document.getElementById('generate-keys').addEventListener('click', generateKeys);
document.getElementById('remove-keys').addEventListener('click', removeKeys);
document.getElementById('copy-public-key').addEventListener('click', copyPublicKey);
