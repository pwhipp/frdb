const activeFilters = {};
const filterHighlightTerms = readEmbeddedJson("filterHighlightTermsData");
let filterOptions = {}, filterCounts = {}, publicationFiltersByAuthor = new Map(), filterModal, currentFilterField = null, table;

document.addEventListener("DOMContentLoaded", async () => {
    filterModal = new bootstrap.Modal(document.getElementById("filterModal"));
    attachFilterModalEvents();

    const response = await fetch("/api/research-data");
    if (!response.ok) {
        throw new Error(`Could not load research data: ${response.status}`);
    }

    const payload = await response.json();
    filterOptions = payload.filters;
    publicationFiltersByAuthor = buildPublicationFiltersByAuthor(payload.publication_filters);
    filterCounts = buildFilterCounts();
    initialiseTable(payload.rows);
});

function initialiseTable(rows) {
    table = new Tabulator("#researchTable", {
        data: rows,
        height: "100%",
        layout: "fitData",
        movableColumns: true,
        placeholder: "No matching studies",
        columns: publicationColumns(),
    });

    table.on("tableBuilt", () => {
        applyFilters();
        updateFilterButtons();
    });
    table.on("dataFiltered", (filters, matchingRows) => updateRowCount(matchingRows.length, rows.length));
    updateRowCount(rows.length, rows.length);
}

function publicationColumns() {
    return [
        authorColumn(),
        textColumn("No. of samples", "sample_count", 125),
        filterColumn("Recovery methods", "recovery_methods", 185),
        filterColumn("Equipment tested", "equipment_tested", 280),
        filterColumn("Biological material", "biological_material", 190),
        filterColumn("Substrate type", "substrate_type", 150),
        textColumn("Substrate descriptions", "substrate_descriptions", 280),
        {
            title: "Statistical analysis",
            field: "statistical_analysis",
            width: 160,
            formatter: statisticalFormatter,
        },
        textColumn("STR analysis", "str_analysis", 115),
        textColumn("Results", "results", 820),
    ];
}

function authorColumn() {
    return {
        title: "Authors",
        field: "authors",
        width: 185,
        frozen: true,
        formatter: authorFormatter,
    };
}

function textColumn(title, field, width) {
    return {title, field, width, formatter: plainPreWrapFormatter(field)};
}

function filterColumn(title, field, width) {
    return {
        title,
        titleFormatter: () => filterTitle(title, field),
        field,
        width,
        formatter: filterableCellFormatter(field),
    };
}

function filterTitle(title, field) {
    return `
        <div class="column-title">
            <span class="column-title-label">${escapeHtml(title)}</span>
            <button class="filter-trigger" type="button" data-filter-field="${field}" aria-label="Filter ${escapeHtml(title)}" title="Filter ${escapeHtml(title)}">▾</button>
        </div>
    `;
}

function authorFormatter(cell) {
    const row = cell.getData();
    const text = escapeHtml(row.authors);
    if (!row.source_url) {
        return `<span class="cell-prewrap">${text}</span>`;
    }
    return `<a class="authors-link cell-prewrap" href="${escapeAttribute(row.source_url)}" target="_blank" rel="noopener noreferrer">${text}</a>`;
}

function plainPreWrapFormatter(field) {
    return (cell) => `<div class="cell-prewrap">${escapeHtml(cell.getData()[field] || "")}</div>`;
}

function filterableCellFormatter(activeFilterField) {
    return (cell) => {
        const row = cell.getData();
        const selected = activeFilters[activeFilterField];
        const filterItems = publicationFilterValues(row.authors, activeFilterField);
        const matchedItems = selected === undefined
            ? []
            : filterItems.filter((item) => selected.has(item));
        const wrapper = document.createElement("div");
        wrapper.className = "cell-prewrap";
        wrapper.textContent = row[activeFilterField] || "";

        if (matchedItems.length) {
            highlightFilterTerms(wrapper, activeFilterField, matchedItems);
        }

        return wrapper;
    };
}

function highlightFilterTerms(container, filterField, matchedItems) {
    const terms = matchedItems.flatMap((item) => filterHighlightTerms[filterField]?.[item] || [item]);
    const pattern = highlightPattern(terms);
    if (!pattern) {
        return;
    }

    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (walker.nextNode()) {
        textNodes.push(walker.currentNode);
    }

    for (const textNode of textNodes) {
        replaceTextMatches(textNode, pattern);
    }
}

function highlightPattern(terms) {
    const uniqueTerms = [...new Set(terms.filter(Boolean))]
        .sort((first, second) => second.length - first.length);
    if (!uniqueTerms.length) {
        return null;
    }

    const escapedTerms = uniqueTerms.map((term) => escapeRegExp(term));
    return new RegExp(`(^|[^\\p{L}\\p{N}-])(${escapedTerms.join("|")})(?=$|[^\\p{L}\\p{N}-])`, "giu");
}

function replaceTextMatches(textNode, pattern) {
    const text = textNode.nodeValue;
    const fragment = document.createDocumentFragment();
    let lastIndex = 0;
    let match;

    pattern.lastIndex = 0;
    while ((match = pattern.exec(text)) !== null) {
        const prefix = match[1] || "";
        const value = match[2];
        const valueStart = match.index + prefix.length;
        const valueEnd = valueStart + value.length;

        fragment.append(document.createTextNode(text.slice(lastIndex, valueStart)));
        const strong = document.createElement("strong");
        strong.className = "cell-filter-match";
        strong.textContent = text.slice(valueStart, valueEnd);
        fragment.append(strong);
        lastIndex = valueEnd;
    }

    if (lastIndex === 0) {
        return;
    }

    fragment.append(document.createTextNode(text.slice(lastIndex)));
    textNode.parentNode.replaceChild(fragment, textNode);
}

function statisticalFormatter(cell) {
    const row = cell.getData();
    const bandClass = row.replicate_band_key ? ` band-${row.replicate_band_key}` : "";
    const label = row.replicate_band ? ` title="${escapeAttribute(row.replicate_band)}"` : "";
    return `<span class="stat-cell${bandClass}"${label}>${escapeHtml(row.statistical_analysis || "")}</span>`;
}

document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-field]");
    if (!button) {
        return;
    }
    event.preventDefault();
    event.stopPropagation();
    openFilterModal(button.dataset.filterField);
}, true);

function attachFilterModalEvents() {
    document.getElementById("applyFilterButton").addEventListener("click", applyCurrentModalFilter);
    document.getElementById("selectAllButton").addEventListener("click", () => setAllVisibleOptions(true));
    document.getElementById("selectNoneButton").addEventListener("click", () => setAllVisibleOptions(false));
    document.getElementById("clearFiltersButton").addEventListener("click", clearAllFilters);
    document.getElementById("filterSearch").addEventListener("input", () => renderFilterOptions());
}

function openFilterModal(field) {
    currentFilterField = field;
    const options = filterOptions[field] || [];
    const active = activeFilters[field];
    const selected = active === undefined ? new Set(options) : new Set(active);

    document.getElementById("filterModalTitle").textContent = titleForFilterField(field);
    document.getElementById("filterModalSubtitle").textContent = `${options.length} available values`;
    document.getElementById("filterSearch").value = "";
    document.getElementById("filterOptions").dataset.selected = JSON.stringify([...selected]);
    renderFilterOptions();
    filterModal.show();
}

function renderFilterOptions() {
    const container = document.getElementById("filterOptions");
    const query = document.getElementById("filterSearch").value.trim().toLowerCase();
    const selected = new Set(JSON.parse(container.dataset.selected || "[]"));
    const options = (filterOptions[currentFilterField] || []).filter((option) => option.toLowerCase().includes(query));

    container.replaceChildren();
    for (const option of options) {
        const id = `filter-${currentFilterField}-${slugify(option)}`;
        const wrapper = document.createElement("label");
        wrapper.className = "filter-option";
        wrapper.setAttribute("for", id);

        const checkbox = document.createElement("input");
        checkbox.className = "form-check-input";
        checkbox.type = "checkbox";
        checkbox.id = id;
        checkbox.value = option;
        checkbox.checked = selected.has(option);
        checkbox.addEventListener("change", () => {
            const updated = new Set(JSON.parse(container.dataset.selected || "[]"));
            if (checkbox.checked) {
                updated.add(option);
            } else {
                updated.delete(option);
            }
            container.dataset.selected = JSON.stringify([...updated]);
        });

        const label = document.createElement("span");
        label.className = "filter-option-label";
        label.textContent = option;

        const count = document.createElement("span");
        count.className = "filter-option-count";
        count.textContent = filterCounts[currentFilterField]?.[option] || 0;

        wrapper.append(checkbox, label, count);
        container.append(wrapper);
    }
}

function applyCurrentModalFilter() {
    const options = filterOptions[currentFilterField] || [];
    const selected = new Set(JSON.parse(document.getElementById("filterOptions").dataset.selected || "[]"));
    activeFilters[currentFilterField] = selected.size === options.length ? undefined : selected;
    applyFilters();
    updateFilterButtons();
    filterModal.hide();
}

function setAllVisibleOptions(checked) {
    const container = document.getElementById("filterOptions");
    const selected = new Set(JSON.parse(container.dataset.selected || "[]"));
    for (const checkbox of container.querySelectorAll("input[type='checkbox']")) {
        checkbox.checked = checked;
        if (checked) {
            selected.add(checkbox.value);
        } else {
            selected.delete(checkbox.value);
        }
    }
    container.dataset.selected = JSON.stringify([...selected]);
}

function clearAllFilters() {
    for (const field of Object.keys(filterOptions)) {
        activeFilters[field] = undefined;
    }
    applyFilters();
    updateFilterButtons();
}

function applyFilters() {
    if (!table) {
        return;
    }
    table.setFilter((row) => {
        for (const field of Object.keys(filterOptions)) {
            const selected = activeFilters[field];
            if (selected === undefined) {
                continue;
            }
            const values = publicationFilterValues(row.authors, field);
            if (!values.some((value) => selected.has(value))) {
                return false;
            }
        }
        return true;
    });
}

function updateFilterButtons() {
    for (const button of document.querySelectorAll("[data-filter-field]")) {
        const field = button.dataset.filterField;
        const selected = activeFilters[field];
        const isActive = selected !== undefined;
        button.classList.toggle("is-active", isActive);
        if (button.classList.contains("filter-trigger")) {
            button.textContent = isActive ? selected.size : "▾";
        }
        const count = button.querySelector(".filter-pill-count");
        if (count) {
            count.textContent = isActive ? selected.size : "";
        }
    }
    if (table) {
        table.redraw(true);
    }
}

function updateRowCount(filteredCount, totalCount) {
    document.getElementById("rowCount").textContent = `${filteredCount}/${totalCount} rows`;
}

function buildFilterCounts() {
    const counts = {};
    for (const field of Object.keys(filterOptions)) {
        counts[field] = {};
        for (const option of filterOptions[field] || []) {
            counts[field][option] = 0;
        }
        for (const publicationFilters of publicationFiltersByAuthor.values()) {
            for (const value of publicationFilters[field] || []) {
                counts[field][value] = (counts[field][value] || 0) + 1;
            }
        }
    }
    return counts;
}

function buildPublicationFiltersByAuthor(publicationFilters) {
    const filtersByAuthor = new Map();
    for (const publicationFilter of publicationFilters || []) {
        filtersByAuthor.set(publicationFilter.authors, publicationFilter);
    }
    return filtersByAuthor;
}

function publicationFilterValues(authors, field) {
    return publicationFiltersByAuthor.get(authors)?.[field] || [];
}

function titleForFilterField(field) {
    return field.replaceAll("_", " ").replace(/^\w/, (letter) => letter.toUpperCase());
}

function readEmbeddedJson(id) {
    const element = document.getElementById(id);
    return element ? JSON.parse(element.textContent) : {};
}

function slugify(value) {
    return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
}

function escapeRegExp(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
