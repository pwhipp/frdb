import {escapeAttribute, escapeHtml} from "./html.js";

const activeScoreKey = new URLSearchParams(window.location.search).get("score_key");
const activeContributionKey = new URLSearchParams(window.location.search).get("contribution_key");

export function initialiseTable(payload, publicationController) {
    const rows = payload.rows || [];
    const columns = payload.table.columns || [];
    const urlRowFilter = rowFilterFromUrl();
    const table = new Tabulator("#researchTable", {
        data: rows,
        height: "100%",
        layout: "fitData",
        movableColumns: true,
        placeholder: "No matching rows",
        columns: buildColumns(columns, publicationController),
    });

    table.on("tableBuilt", () => {
        if (publicationController) {
            publicationController.attach(table);
            publicationController.applyFilters();
            publicationController.updateFilterButtons();
        }
        if (urlRowFilter) {
            table.setFilter(urlRowFilter);
        }
        attachDetailColumnToggle(table, columns);
    });
    table.on("dataFiltered", (filters, matchingRows) => updateRowCount(matchingRows.length, rows.length));
    updateRowCount(rows.length, rows.length);
    return table;
}

function rowFilterFromUrl() {
    if (activeContributionKey) {
        return (row) => (row.contribution_keys || []).includes(activeContributionKey);
    }
    if (!activeScoreKey) {
        return null;
    }
    return (row) => Object.hasOwn(row.score_contributions || {}, activeScoreKey);
}

function buildColumns(columns, publicationController) {
    return columns.map((column) => columnDefinition(column, publicationController));
}

function columnDefinition(column, publicationController) {
    const definition = {
        title: column.title,
        field: column.field,
        width: column.width,
        frozen: Boolean(column.frozen),
        visible: !column.default_hidden,
        formatter: plainPreWrapFormatter(column.field),
    };

    if (column.formatter === "authors") {
        definition.formatter = authorFormatter;
    } else if (column.formatter === "publication_link") {
        definition.formatter = publicationLinkFormatter(column.field);
    } else if (column.formatter === "score_contribution") {
        definition.formatter = scoreContributionFormatter(column.field);
    } else if (column.formatter === "statistical") {
        definition.formatter = statisticalFormatter;
    }

    if (column.filterable && publicationController) {
        definition.titleFormatter = () => publicationController.filterTitle(column.title, column.field);
        definition.formatter = publicationController.filterableCellFormatter(column.field);
    }
    return definition;
}

function attachDetailColumnToggle(table, columns) {
    const button = document.getElementById("detailColumnsButton");
    const fields = columns.filter((column) => column.default_hidden).map((column) => column.field);
    if (!button || fields.length === 0) {
        return;
    }

    let detailsVisible = false;
    button.classList.remove("d-none");
    button.addEventListener("click", () => {
        detailsVisible = !detailsVisible;
        for (const field of fields) {
            const column = table.getColumn(field);
            if (!column) {
                continue;
            }
            if (detailsVisible) {
                column.show();
            } else {
                column.hide();
            }
        }
        updateDetailColumnButton(button, detailsVisible);
    });
    updateDetailColumnButton(button, detailsVisible);
}

function updateDetailColumnButton(button, detailsVisible) {
    button.textContent = detailsVisible ? "Hide details" : "Show details";
    button.setAttribute("aria-pressed", String(detailsVisible));
}

function authorFormatter(cell) {
    const row = cell.getData();
    const text = escapeHtml(row.authors || "");
    if (!row.source_url) {
        return `<span class="cell-prewrap">${text}</span>`;
    }
    return `<a class="authors-link cell-prewrap" href="${escapeAttribute(row.source_url)}" target="_blank" rel="noopener noreferrer">${text}</a>`;
}

function publicationLinkFormatter(field) {
    return (cell) => {
        const row = cell.getData();
        const text = escapeHtml(row[field] || "");
        if (!row.publication_id) {
            return `<span class="cell-prewrap">${text}</span>`;
        }
        return `<a class="authors-link cell-prewrap" href="/tables/publications?study_ids=${Number(row.publication_id)}">${text}</a>`;
    };
}

function scoreContributionFormatter(field) {
    return (cell) => {
        const row = cell.getData();
        if (activeScoreKey && Object.hasOwn(row.score_contributions || {}, activeScoreKey)) {
            return `<span class="cell-prewrap">${formatSignedNumber(row.score_contributions[activeScoreKey])}</span>`;
        }
        return `<div class="cell-prewrap">${escapeHtml(row[field] || "")}</div>`;
    };
}

function plainPreWrapFormatter(field) {
    return (cell) => `<div class="cell-prewrap">${escapeHtml(cell.getData()[field] || "")}</div>`;
}

function formatSignedNumber(value) {
    return Number(value).toLocaleString("en", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
        signDisplay: "always",
    });
}

function statisticalFormatter(cell) {
    const row = cell.getData();
    const bandClass = row.replicate_band_key ? ` band-${row.replicate_band_key}` : "";
    const label = row.replicate_band ? ` title="${escapeAttribute(row.replicate_band)}"` : "";
    return `<span class="stat-cell${bandClass}"${label}>${escapeHtml(row.statistical_analysis || "")}</span>`;
}

function updateRowCount(filteredCount, totalCount) {
    document.getElementById("rowCount").textContent = `${filteredCount}/${totalCount} rows`;
}
