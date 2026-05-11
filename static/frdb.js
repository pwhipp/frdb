const filterFields = {
    recovery_methods: {
        title: "Recovery methods",
        rowField: "recovery_methods_filter",
    },
    equipment_tested: {
        title: "Equipment tested",
        rowField: "equipment_tested_filter",
    },
    biological_material: {
        title: "Biological material",
        rowField: "biological_material_filter",
    },
    substrate_type: {
        title: "Substrate type",
        rowField: "substrate_type_filter",
    },
};

const activeFilters = {};
const resultColumnWidth = 820;
const filterHighlightTerms = {
    recovery_methods: {
        "Swabbing": ["swabbing", "swab"],
        "Tape-lifting": ["tape-lifting", "tape lifting", "tape-lift", "tape lift"],
        "Vacuum": ["vacuum", "m-vac"],
        "Excising": ["excising", "excise"],
        "Soaking": ["soaking", "soak"],
        "Direct lysis": ["direct lysis"],
        "Direct PCR": ["direct pcr"],
        "FTA paper-scraping": ["fta paper-scraping", "fta", "paper-scraping"],
        "Scraping": ["scraping", "scrape"],
        "Plasti dip": ["plasti dip"],
        "Untreated filter paper": ["untreated filter paper", "filter paper"],
        "Direct extraction": ["direct extraction"],
        "Cell elution": ["cell elution"],
    },
    equipment_tested: {
        "Cotton swab": ["cotton swab", "cotton", "150c"],
        "Nylon/flocked swab": ["nylon", "flocked", "floq", "flock"],
        "Rayon swab": ["rayon"],
        "Foam swab": ["foam"],
        "Polyester swab": ["polyester"],
        "Tape lift/minitape": ["tape lift", "tape-lift", "minitape", "mini-tape", "gellifter", "instant lifter"],
        "Adhesive tape": ["adhesive tape", "scotch", "sellotape", "masking tape"],
        "M-Vac/wet vacuum": ["m-vac", "wet vacuum", "wet-vacuum"],
        "Dry vacuum": ["dry vacuum", "dna buster"],
        "Pulse lavage": ["pulse lavage", "interpulse", "pulsavac"],
        "Direct PCR/microFLOQ": ["direct pcr", "microfloq"],
        "Filter/FTA paper": ["filter paper", "fta", "whatman"],
        "Scraping/excision": ["scraping", "excising", "excision"],
        "Direct lysis/extraction": ["direct lysis", "direct extraction", "autolys", "prepfiler", "ez1"],
        "Soaking/rinse": ["soaking", "rinse", "atl buffer", "btmix"],
    },
    biological_material: {
        "Touch DNA": ["touch dna", "tdna"],
        "Blood": ["blood", "buffy coat"],
        "Saliva": ["saliva"],
        "Buccal cells": ["buccal"],
        "gDNA": ["gdna"],
        "Extracted DNA": ["extracted dna", "dna isolate"],
        "cfDNA": ["cfdna"],
        "Semen": ["semen"],
        "Sweat": ["sweat"],
        "Buffy coat": ["buffy coat"],
        "Various": ["various"],
    },
    substrate_type: {
        "Porous": ["porous"],
        "Non-porous": ["non-porous"],
        "n/a": ["n/a"],
    },
};
let filterOptions = {};
let filterCounts = {};
let filterModal;
let currentFilterField = null;
let table;

document.addEventListener("DOMContentLoaded", async () => {
    filterModal = new bootstrap.Modal(document.getElementById("filterModal"));
    attachFilterModalEvents();

    const response = await fetch("/api/research-data");
    if (!response.ok) {
        throw new Error(`Could not load research data: ${response.status}`);
    }

    const payload = await response.json();
    filterOptions = payload.filters;
    filterCounts = buildFilterCounts(payload.rows);
    initialiseTable(payload.rows);
});

function initialiseTable(rows) {
    table = new Tabulator("#researchTable", {
        data: rows,
        height: "100%",
        layout: "fitData",
        movableColumns: true,
        placeholder: "No matching studies",
        columns: [
            {
                title: "Authors",
                field: "authors",
                width: 185,
                frozen: true,
                formatter: authorFormatter,
            },
            {
                title: "No. of samples",
                field: "sample_count",
                width: 125,
                formatter: plainPreWrapFormatter("sample_count_html"),
            },
            {
                title: "Recovery methods",
                titleFormatter: () => filterTitle("Recovery methods", "recovery_methods"),
                field: "recovery_methods",
                width: 185,
                formatter: filterableCellFormatter("recovery_methods_html", "recovery_methods", "recovery_methods_filter"),
            },
            {
                title: "Equipment tested",
                titleFormatter: () => filterTitle("Equipment tested", "equipment_tested"),
                field: "equipment_tested",
                width: 280,
                formatter: filterableCellFormatter("equipment_tested_html", "equipment_tested", "equipment_tested_filter"),
            },
            {
                title: "Biological material",
                titleFormatter: () => filterTitle("Biological material", "biological_material"),
                field: "biological_material",
                width: 190,
                formatter: filterableCellFormatter("biological_material_html", "biological_material", "biological_material_filter"),
            },
            {
                title: "Substrate type",
                titleFormatter: () => filterTitle("Substrate type", "substrate_type"),
                field: "substrate_type",
                width: 150,
                formatter: filterableCellFormatter("substrate_type_html", "substrate_type", "substrate_type_filter"),
            },
            {
                title: "Substrate descriptions",
                field: "substrate_descriptions",
                width: 280,
                formatter: plainPreWrapFormatter("substrate_descriptions_html"),
            },
            {
                title: "Statistical analysis",
                field: "statistical_analysis",
                width: 160,
                formatter: statisticalFormatter,
            },
            {
                title: "STR analysis",
                field: "str_analysis",
                width: 115,
                formatter: plainPreWrapFormatter("str_analysis_html"),
            },
            {
                title: "Results",
                field: "results",
                width: resultColumnWidth,
                formatter: plainPreWrapFormatter("results_html"),
            },
        ],
    });

    table.on("tableBuilt", () => {
        applyFilters();
        updateFilterButtons();
    });
    table.on("dataFiltered", (filters, matchingRows) => updateRowCount(matchingRows.length, rows.length));
    updateRowCount(rows.length, rows.length);
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

function plainPreWrapFormatter(htmlField) {
    return (cell) => `<div class="cell-prewrap">${cell.getData()[htmlField] || ""}</div>`;
}

function filterableCellFormatter(htmlField, activeFilterField, rowFilterField) {
    return (cell) => {
        const row = cell.getData();
        const selected = activeFilters[activeFilterField];
        const filterItems = row[rowFilterField] || [];
        const matchedItems = selected === undefined
            ? []
            : filterItems.filter((item) => selected.has(item));
        const wrapper = document.createElement("div");
        wrapper.className = "cell-prewrap";
        wrapper.innerHTML = row[htmlField] || "";

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
    return `<span class="stat-cell${bandClass}"${label}>${row.statistical_analysis_html || ""}</span>`;
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
    const definition = filterFields[field];
    const options = filterOptions[field] || [];
    const active = activeFilters[field];
    const selected = active === undefined ? new Set(options) : new Set(active);

    document.getElementById("filterModalTitle").textContent = definition.title;
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
    for (const field of Object.keys(filterFields)) {
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
        for (const [field, definition] of Object.entries(filterFields)) {
            const selected = activeFilters[field];
            if (selected === undefined) {
                continue;
            }
            const values = row[definition.rowField] || [];
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

function buildFilterCounts(rows) {
    const counts = {};
    for (const [field, definition] of Object.entries(filterFields)) {
        counts[field] = {};
        for (const option of filterOptions[field] || []) {
            counts[field][option] = 0;
        }
        for (const row of rows) {
            for (const value of row[definition.rowField] || []) {
                counts[field][value] = (counts[field][value] || 0) + 1;
            }
        }
    }
    return counts;
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
