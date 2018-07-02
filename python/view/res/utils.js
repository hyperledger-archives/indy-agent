function removeElementById(id) {
    // removes element from DOM by its ID
    var element = document.getElementById(id);
    element.parentNode.removeChild(element);
}