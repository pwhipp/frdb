import {escapeHtml, escapeRegExp, slugify} from "./html.js";

export function createPublicationController(payload, filterHighlightTerms) {
    const filterOptions = payload.filters || {};
    const activeFilters = {};
    const publicationFiltersByAuthor = buildPublicationFiltersByAuthor(payload.publication_filters || []);
    const filterCounts = buildFilterCounts(filterOptions, publicationFiltersByAuthor);
    const selectedStudyIds = studyIdsFromUrl();
    let filterModal = null;
    let currentFilterField = null;
    let table = null;

    function attach(tabulatorTable) {
        table = tabulatorTable;
        const modalElement = document.getElementById("filterModal");
        if (modalElement) {
            filterModal = new bootstrap.Modal(modalElement);
            attachFilterModalEvents();
        }
    }

    function filterTitle(title, field) {
        return `
            <div class="column-title">
                <span class="column-title-label">${escapeHtml(title)}</span>
                <button class="filter-trigger" type="button" data-filter-field="${field}" aria-label="Filter ${escapeHtml(title)}" title="Filter ${escapeHtml(title)}">▾</button>
            </div>
        `;
    }

    function filterableCellFormatter(activeFilterField) {
        return (cell) => {
            const row = cell.getData();
            const selected = activeFilters[activeFilterField];
            const filterItems = publicationFilterValues(publicationFiltersByAuthor, row.authors, activeFilterField);
            const matchedItems = selected === undefined ? [] : filterItems.filter((item) => selected.has(item));
            const wrapper = document.createElement("div");
            wrapper.className = "cell-prewrap";
            wrapper.textContent = row[activeFilterField] || "";

            if (matchedItems.length) {
                highlightFilterTerms(wrapper, activeFilterField, matchedItems, filterHighlightTerms);
            }
            return wrapper;
        };
    }

    function attachFilterModalEvents() {
        document.getElementById("applyFilterButton").addEventListener("click", applyCurrentModalFilter);
        document.getElementById("filterSelectHeading").addEventListener("change", (event) => setAllVisibleOptions(event.target.checked));
        document.getElementById("clearFiltersButton").addEventListener("click", clearAllFilters);
        document.getElementById("filterSearch").addEventListener("input", () => renderFilterOptions());
        document.addEventListener("click", handleFilterTriggerClick, true);
    }

    function handleFilterTriggerClick(event) {
        const button = event.target.closest("[data-filter-field]");
        if (!button || !filterModal) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        openFilterModal(button.dataset.filterField);
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
            container.append(filterOption(option, selected, container));
        }
        updateFilterSelectHeading();
    }

    function filterOption(option, selected, container) {
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
        checkbox.addEventListener("change", () => updateSelectedOption(checkbox, option, container));
        const label = document.createElement("span");
        label.className = "filter-option-label";
        label.textContent = option;
        const count = document.createElement("span");
        count.className = "filter-option-count";
        count.textContent = filterCounts[currentFilterField]?.[option] || 0;
        wrapper.append(checkbox, label, count);
        return wrapper;
    }

    function updateSelectedOption(checkbox, option, container) {
        const updated = new Set(JSON.parse(container.dataset.selected || "[]"));
        if (checkbox.checked) {
            updated.add(option);
        } else {
            updated.delete(option);
        }
        container.dataset.selected = JSON.stringify([...updated]);
        updateFilterSelectHeading();
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
        const action = checked ? "add" : "delete";
        for (const checkbox of container.querySelectorAll("input[type='checkbox']")) {
            checkbox.checked = checked;
            selected[action](checkbox.value);
        }
        container.dataset.selected = JSON.stringify([...selected]);
        updateFilterSelectHeading();
    }

    function updateFilterSelectHeading() {
        const heading = document.getElementById("filterSelectHeading");
        const count = document.getElementById("filterSelectHeadingCount");
        const checkboxes = [...document.querySelectorAll("#filterOptions input[type='checkbox']")];
        const checkedCount = checkboxes.filter((checkbox) => checkbox.checked).length;
        heading.disabled = checkboxes.length === 0;
        heading.checked = checkboxes.length > 0 && checkedCount === checkboxes.length;
        heading.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
        count.textContent = `${checkedCount}/${checkboxes.length} selected`;
    }

    function clearAllFilters() {
        for (const field of Object.keys(filterOptions)) {
            activeFilters[field] = undefined;
        }
        selectedStudyIds.clear();
        window.history.replaceState(null, "", window.location.pathname);
        applyFilters();
        updateFilterButtons();
    }

    function applyFilters() {
        if (!table) {
            return;
        }
        table.setFilter((row) => publicationRowMatches(row));
    }

    function publicationRowMatches(row) {
        if (selectedStudyIds.size) {
            return selectedStudyIds.has(Number(row.id));
        }
        for (const field of Object.keys(filterOptions)) {
            const selected = activeFilters[field];
            if (selected === undefined) {
                continue;
            }
            const values = publicationFilterValues(publicationFiltersByAuthor, row.authors, field);
            if (!values.some((value) => selected.has(value))) {
                return false;
            }
        }
        return true;
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

    return {attach, applyFilters, filterTitle, filterableCellFormatter, updateFilterButtons};
}

function studyIdsFromUrl() {
    const values = new URLSearchParams(window.location.search).get("study_ids");
    if (!values) {
        return new Set();
    }
    return new Set(values.split(",").map((value) => Number(value)).filter(Number.isInteger));
}

function highlightFilterTerms(container, filterField, matchedItems, filterHighlightTerms) {
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
    const uniqueTerms = [...new Set(terms.filter(Boolean))].sort((first, second) => second.length - first.length);
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
        const valueStart = match.index + prefix.length;
        const valueEnd = valueStart + match[2].length;
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

function buildFilterCounts(filterOptions, publicationFiltersByAuthor) {
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

function publicationFilterValues(publicationFiltersByAuthor, authors, field) {
    return publicationFiltersByAuthor.get(authors)?.[field] || [];
}

function titleForFilterField(field) {
    return field.replaceAll("_", " ").replace(/^\w/, (letter) => letter.toUpperCase());
}
