import {readEmbeddedJson} from "./html.js";
import {createPublicationController} from "./publications.js";
import {initialiseTable} from "./table.js";

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startTablePage);
} else {
    startTablePage();
}

async function startTablePage() {
    const shell = document.querySelector(".table-shell");
    if (!shell) {
        return;
    }

    const tableId = shell.dataset.tableId;
    const response = await fetch(`/api/tables/${tableId}`);
    if (!response.ok) {
        throw new Error(`Could not load table data: ${response.status}`);
    }

    const payload = await response.json();
    const publicationController = payload.table.special_filters
        ? createPublicationController(payload, readEmbeddedJson("filterHighlightTermsData"))
        : null;
    initialiseTable(payload, publicationController);
}
