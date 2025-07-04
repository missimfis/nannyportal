function showPreview(event) {
    if (event.target.files.length > 0) {
        let blob = event.target.files[0];
        let src = null;
        if (window.webkitURL) {
            src = window.webkitURL.createObjectURL(blob);
        } else if (window.URL && window.URL.createObjectURL) {
            src = window.URL.createObjectURL(blob);
        }

        let preview = document.getElementById("file-ip-1-preview");
        preview.src = src;
        preview.style.display = "block";
    }
}

function deleteImage() {
    let preview = document.getElementById("file-ip-1-preview");
    preview.src = "/media/web/images/mitarbeiter.png";

    /*let element = document.getElementById("file-ip-1");
    if (element.target.files.length > 0) {
        console.log(element.target.files.pop());
    }*/
}