/**
 * für die hidden checkboxen Logik das markiert wenn aktiviert
 */
function changeCheckedClass(id) {
    if (document.getElementById(id).className.includes("betreuungsart-button-active")) {
        document.getElementById(id).className = document.getElementById(id).className.replace(" betreuungsart-button-active", "")
    } else {
        document.getElementById(id).className = document.getElementById(id).className + " betreuungsart-button-active";
    }
}
document.addEventListener("DOMContentLoaded", function(event) {
    Array.from(document.getElementsByClassName("betreuungsart-button")).forEach(element => {
        if (document.getElementsByName(element.id)[0].checked) {
            element.className = element.className + " betreuungsart-button-active";
        }
    });
    if (window.location.href.includes("/nachrichten/")) {
        checkNachrichtenLink();
        scrollToBottomOfDiv();
        expandTextarea('id_meldung');
        attachEventToScope();
        onReseizeCheckClass();
    }
});

function checkNachrichtenLink() {
    let link = window.location.href;
    if (window.innerWidth < 1050 && link.includes("/nachrichten/")) {
        if (link.includes("?message=true")) {
            var aNode = document.createElement("a");
            aNode.href = link.replace("?message=true", "");
            aNode.classList.add("zurueckbutton");
            aNode.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-chevron-compact-left" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M9.224 1.553a.5.5 0 0 1 .223.67L6.56 8l2.888 5.776a.5.5 0 1 1-.894.448l-3-6a.5.5 0 0 1 0-.448l3-6a.5.5 0 0 1 .67-.223z"/></svg>';
            let divMessageBack = document.getElementById("messageBack");
            divMessageBack.insertBefore(aNode, divMessageBack.firstChild);
            removeClassfromQuery(".col-sm-9.hidden", "hidden");
            addClassfromQuery(".col-sm-3", "hidden");
        } else {
            removeClassfromQuery(".col-sm-3.hidden", "hidden");
            addClassfromQuery(".col-sm-9", "hidden");
        }
    }
}

function removeClassfromQuery(query, className) {
    var elems = document.querySelectorAll(query);

    [].forEach.call(elems, function(el) {
        el.classList.remove(className);
    });
}

function addClassfromQuery(query, className) {
    var elems = document.querySelectorAll(query);

    [].forEach.call(elems, function(el) {
        el.classList.add(className);
    });
}

function scrollToBottomOfDiv() {
    var objDiv = document.getElementById("messageContainer");
    objDiv.scrollTop = objDiv.scrollHeight;
}

function expandTextarea(id) {
    var element = document.getElementById(id);
    element.addEventListener('keyup', adjustTextareaHeight, false);
    element.addEventListener('input', adjustTextareaHeight, false);
}

function adjustTextareaHeight() {
    if (Object.is(NaN, this.style.height) || this.value == '') {
        this.style.height = 0;
    } else if (parseInt(this.scrollHeight, 10) < 400) {
        this.style.height = this.scrollHeight + 'px';
        this.scrollTop = this.scrollHeight;
    }
}

function spinner(id) {
    document.getElementById(id).innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span><span>send...</span>';
    document.getElementById(id).disabled = true;
    document.getElementById('suchen_form').submit();
}

function onReseizeCheckClass() {
    var element = document.getElementById("message-form");
    if (window.innerWidth < 1050) {
        element.className = "farbe fixed-bottom"
    } else {
        element.className = "farbe"
    }
}

function attachEventToScope() {
    if (window.attachEvent) {
        window.attachEvent('onresize', onReseizeCheckClass);
    } else if (window.addEventListener) {
        window.addEventListener('resize', onReseizeCheckClass, true);
    } else {
        //The browser does not support Javascript event binding
    }
}