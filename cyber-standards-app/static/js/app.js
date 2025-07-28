// Global variables for data (initialized later inside initializeApp)
let standardsData = [];
let lastQuery = '';

// --- Helper Functions ---

/**
 * Displays a loading spinner in the results container.
 */
function showLoadingSpinner() {
    const resultsList = document.getElementById('resultsContainer');
    if (resultsList) {
        resultsList.innerHTML = '<div class="flex justify-center py-8"><div class="loader"></div></div>';
    }
}

/**
 * Hides the loading spinner by clearing the results container.
 */
function hideLoadingSpinner() {
    const resultsList = document.getElementById('resultsContainer');
    if (resultsList) {
        resultsList.innerHTML = '';
    }
}

/**
 * Highlights a given term within a text string using <mark> tags.
 * @param {string} text - The original text to search within.
 * @param {string} term - The term to highlight.
 * @returns {string} The text with the term highlighted.
 */
function highlightTerm(text, term) {
    if (!term || !text) return text;
    // Escape special characters in the term for regex to prevent errors
    const escapedTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escapedTerm})`, 'gi'); // 'gi' for global and case-insensitive
    return text.replace(regex, '<mark class="bg-yellow-200">$&</mark>');
}

/**
 * Fetches standards data from the backend API based on provided filters.
 * Displays loading spinner, fetches data, then calls displayResults.
 * @param {string} query - The search query string.
 * @param {string} section - The selected section filter.
 * @param {string} source - The selected source filter.
 */
async function fetchStandardsData(query = '', section = '', source = '') {
    showLoadingSpinner(); // Show spinner immediately

    const queryParams = new URLSearchParams();
    if (query && query.trim() !== '') queryParams.append('query', query.trim());
    if (section && section.trim() !== '') queryParams.append('section', section.trim());
    if (source && source.trim() !== '') queryParams.append('source', source.trim());

    const url = `/api/standards?${queryParams.toString()}`;
    console.log("Fetching data from:", url); // Debugging: log the URL being fetched

    try {
        const response = await fetch(url);
        if (!response.ok) {
            const errorText = await response.text(); // Get server's error message
            console.error(`Failed to fetch standards: ${response.status} ${response.statusText}`, errorText);
            throw new Error(`Failed to fetch standards: ${response.statusText}. Server message: ${errorText.substring(0, 200)}...`);
        }
        standardsData = await response.json();
        console.log("Received data:", standardsData); // Debugging: log received data
        displayResults(standardsData, query); // Display results with the current query for highlighting
    } catch (error) {
        console.error('Error fetching standards data:', error);
        const resultsList = document.getElementById('resultsContainer');
        if (resultsList) {
            resultsList.innerHTML = `<p class="text-center text-red-500">Error loading data: ${error.message}. Please check console for details.</p>`;
        }
        standardsData = []; // Clear data on error
    }
}

/**
 * Fetches filter options (sections and sources) from the backend API
 * and populates the respective dropdowns.
 */
async function fetchFilters() {
    try {
        const response = await fetch('/api/filters');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const filters = await response.json();

        const sectionSelect = document.getElementById('sectionDropdown');
        const sourceSelect = document.getElementById('sourceDropdown');

        // Populate Sections dropdown
        if (sectionSelect) {
            // Clear existing options first (except the "All Sections" default)
            sectionSelect.innerHTML = '<option value="">All Sections</option>';
            filters.sections.forEach(section => {
                if (section) { // Only add non-empty sections
                    const option = document.createElement('option');
                    option.value = section;
                    option.textContent = section;
                    sectionSelect.appendChild(option);
                }
            });
        }

        // Populate Sources dropdown
        if (sourceSelect) {
            // Clear existing options first (except the "All Sources" default)
            sourceSelect.innerHTML = '<option value="">All Sources</option>';
            filters.sources.forEach(source => {
                if (source) { // Only add non-empty sources
                    const option = document.createElement('option');
                    option.value = source;
                    option.textContent = source;
                    sourceSelect.appendChild(option);
                }
            });
        }

    } catch (error) {
        console.error('Error fetching filters:', error);
        const resultsList = document.getElementById('resultsContainer');
        if (resultsList) {
            resultsList.innerHTML = `<p class="text-center text-red-500">Could not load filters: ${error.message}.</p>`;
        }
    }
}

/**
 * Displays the fetched search results in the UI.
 * @param {Array<Object>} results - An array of standard objects to display.
 * @param {string} query - The current search query for highlighting.
 */
function displayResults(results, query = '') {
    const resultsList = document.getElementById('resultsContainer');
    if (!resultsList) return; // Ensure resultsList exists

    if (results.length === 0) {
        resultsList.innerHTML = '<p class="text-center text-gray-500 py-4">No results found for your search criteria.</p>';
        return;
    }

    resultsList.innerHTML = ''; // Clear previous results

    results.forEach((item) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'bg-white p-4 rounded-lg shadow mb-4 last:mb-0 border border-gray-200';

        // Prepare highlighted content for all fields
        const highlightedTitle = item.Title ? highlightTerm(item.Title, query) : '';
        const highlightedSource = item.Source ? item.Source : '';
        const highlightedControlID = item.ControlID && item.ControlID !== 'N/A' ? highlightTerm(item.ControlID, query) : '';
        const highlightedSection = item.Section ? highlightTerm(item.Section, query) : '';
        const highlightedRequirementText = item['Requirement Text'] ? highlightTerm(item['Requirement Text'], query) : '';
        const highlightedSimplifiedSummary = item['Simplified Summary'] ? highlightTerm(item['Simplified Summary'], query) : '';
        const highlightedControlCategory = item['Control Category'] ? highlightTerm(item['Control Category'], query) : '';
        const highlightedKeywords = item.Keywords ? highlightTerm(item.Keywords, query) : '';
        const highlightedPageNumber = item['Page Number'] ? highlightTerm(item['Page Number'], query) : '';

        // Function to create a clean metadata row using CSS Grid for precise alignment
        // Labels are given a fixed width (140px) and values take the remaining space.
        // `border-none` explicitly removes any unwanted borders.
        const createMetadataRow = (label, value) => {
            if (!value) return ''; // Don't render if value is empty
            return `
                <div class="grid grid-cols-[140px_1fr] items-start text-sm border-none">
                    <span class="font-semibold text-gray-800">${label}:</span>
                    <span class="text-gray-700">${value}</span>
                </div>
            `;
        };

        resultItem.innerHTML = `
            <div class="flex flex-col">
                <div class="mb-3 pb-2 border-b border-gray-200">
                    <h3 class="text-xl font-bold text-blue-800 break-words pr-2 leading-tight">
                        ${highlightedTitle} <span class="text-gray-500 text-sm font-normal">(${highlightedSource})</span>
                    </h3>
                    ${highlightedRequirementText ? `<p class="mt-2 text-gray-700 leading-snug">${highlightedRequirementText}</p>` : ''}
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2">
                    <div>
                        ${createMetadataRow('Section', highlightedSection)}
                        ${createMetadataRow('Control ID', highlightedControlID)}
                        ${createMetadataRow('Page', highlightedPageNumber)}
                    </div>
                    <div>
                        ${createMetadataRow('Control Category', highlightedControlCategory)}
                        ${createMetadataRow('Keywords', highlightedKeywords)}
                        ${createMetadataRow('Summary', highlightedSimplifiedSummary)}
                    </div>
                </div>
                </div>
        `;
        resultsList.appendChild(resultItem);
    });
}

// --- Event Handling and Initialization ---

/**
 * Handles the search action by reading the input and dropdown values
 * and calling the data fetch function.
 */
function handleSearch() {
    const query = document.getElementById('searchInput').value;
    const section = document.getElementById('sectionDropdown').value;
    const source = document.getElementById('sourceDropdown').value;
    lastQuery = query; // Store the last query for highlighting
    fetchStandardsData(query, section, source);
}

/**
 * Resets all filters and the search query, then reloads the data.
 */
function handleReset() {
    document.getElementById('searchInput').value = '';
    document.getElementById('sectionDropdown').value = '';
    document.getElementById('sourceDropdown').value = '';
    fetchStandardsData();
}

/**
 * Initializes the application by setting up event listeners and fetching filters.
 */
function initializeApp() {
    // Set up event listeners for search
    document.getElementById('searchButton').addEventListener('click', handleSearch);
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });

    // Set up event listeners for dropdowns
    document.getElementById('sectionDropdown').addEventListener('change', handleSearch);
    document.getElementById('sourceDropdown').addEventListener('change', handleSearch);

    // Set up event listener for the reset button
    document.getElementById('resetButton').addEventListener('click', handleReset);

    // Fetch filter options when the page loads
    fetchFilters();

    // Load initial data (or an empty state)
    fetchStandardsData();
}

// Run the initialization function when the document is ready
document.addEventListener('DOMContentLoaded', initializeApp);