// Global variables for DOM elements
const queryInput = document.getElementById('searchInput'); // Corrected ID based on common usage
const sectionSelect = document.getElementById('sectionDropdown');
const sourceSelect = document.getElementById('sourceDropdown');
const resultsList = document.getElementById('resultsContainer');
const resetButton = document.getElementById('resetButton');
const searchButton = document.getElementById('searchButton');
const exportPdfButton = document.getElementById('exportPdfButton'); // Assuming you have this button

let standardsData = []; // To store all data for potential client-side operations

// Fetch standards data from backend API using GET request
async function fetchStandardsData(query = '', section = '', source = '') {
  try {
    resultsList.innerHTML = '<p class="text-gray-600 text-center py-4">Loading results...</p>'; // Show loading indicator

    const queryParams = new URLSearchParams();
    if (query) queryParams.append('query', query);
    // Only append section/source if they are not the 'All' option (which is an empty string value)
    if (section && section !== '') queryParams.append('section', section);
    if (source && source !== '') queryParams.append('source', source);

    const url = `/api/standards?${queryParams.toString()}`;
    const response = await fetch(url);

    if (!response.ok) {
      // Log the full error response from the server for debugging
      const errorText = await response.text();
      console.error(`Failed to fetch standards: ${response.status} ${response.statusText}`, errorText);
      throw new Error(`Failed to fetch standards: ${response.statusText}. Server message: ${errorText.substring(0, 100)}...`);
    }

    const data = await response.json();
    standardsData = data; // Store fetched data
    renderResults(data); // Render the results
    return data;
  } catch (error) {
    console.error('Error fetching standards:', error);
    resultsList.innerHTML = `<p class="text-red-600 text-center">Error loading data: ${error.message}. Please try again or check the server console for details.</p>`;
    return [];
  }
}

// Fetch filter options from backend API
async function fetchFilters() {
  try {
    const response = await fetch('/api/filters');
    if (!response.ok) {
      throw new Error(`Failed to fetch filters: ${response.statusText}`);
    }

    const { sections, sources } = await response.json();

    // Populate Section Dropdown
    sectionSelect.innerHTML = '<option value="">All Sections</option>'; // Value "" means "All"
    if (sections && Array.isArray(sections)) {
        sections.forEach(section => {
            if (section) { // Only add non-empty sections
                sectionSelect.innerHTML += `<option value="${section}">${section}</option>`;
            }
        });
    }

    // Populate Source Dropdown
    sourceSelect.innerHTML = '<option value="">All Sources</option>'; // Value "" means "All"
    if (sources && Array.isArray(sources)) {
        sources.forEach(source => {
            if (source) { // Only add non-empty sources
                sourceSelect.innerHTML += `<option value="${source}">${source}</option>`;
            }
        });
    }

  } catch (error) {
    console.error('Error fetching filters:', error);
    resultsList.innerHTML = `<p class="text-red-600 text-center">Could not load filters: ${error.message}.</p>`;
  }
}

// Render search results
function renderResults(data) {
  if (!data.length) {
    resultsList.innerHTML = '<p class="text-gray-600 text-center py-4">No results found for your search criteria.</p>';
    return;
  }

  resultsList.innerHTML = data.map(item => {
    // Determine the main description to display
    const mainDescription = item.Description || 'No description provided.';
    
    // Only show Requirement Text if it's distinct from the main description
    // and if item['Requirement Text'] actually exists and is not empty
    const requirementTextDisplay = (item['Requirement Text'] && item['Requirement Text'] !== mainDescription && item['Requirement Text'].trim() !== '')
        ? `<p><strong>Requirement:</strong> ${item['Requirement Text']}</p>`
        : '';

    return `
      <div class="p-4 mb-4 bg-white border border-gray-200 rounded shadow-sm">
        <div class="flex flex-wrap items-baseline gap-x-3 mb-2">
            <h3 class="text-lg font-semibold text-blue-800">${item.Title || mainDescription.split('.')[0] || 'No Title Provided'}</h3>
            <span class="text-sm text-gray-600">(${item.Source || 'N/A'})</span>
            <span class="text-xs font-mono text-gray-500 ml-auto">Control ID: ${item.ControlID || 'N/A'}</span>
        </div>
        <p class="text-gray-700 text-sm mb-2">
            ${mainDescription}
        </p>

        <div class="text-gray-700 text-sm grid grid-cols-1 md:grid-cols-2 gap-1 mt-2">
            ${item.Section ? `<p><strong>Section:</strong> ${item.Section}</p>` : ''}
            ${item['Control Category'] ? `<p><strong>Control Category:</strong> ${item['Control Category']}</p>` : ''}
            ${requirementTextDisplay} ${item['Simplified Summary'] ? `<p><strong>Summary:</strong> ${item['Simplified Summary']}</p>` : ''}
            ${item.Keywords ? `<p><strong>Keywords:</strong> ${item.Keywords}</p>` : ''}
            ${item['Page Number'] ? `<p><strong>Page:</strong> ${item['Page Number']}</p>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

// Perform search with current inputs
async function performSearch() {
  const query = queryInput.value.trim();
  const selectedSection = sectionSelect.value;
  const selectedSource = sourceSelect.value;

  await fetchStandardsData(query, selectedSection, selectedSource);
}

// Reset all filters and input
function resetFilters() {
  queryInput.value = '';
  sectionSelect.value = ''; // Set to default 'All Sections'
  sourceSelect.value = '';  // Set to default 'All Sources'
  performSearch(); // Re-fetch data with no filters
}

// Initialize app: Load filters, then perform an initial search
async function initializeApp() {
  console.log("Initializing app...");
  await fetchFilters();     // Wait for dropdowns to populate
  await fetchStandardsData(); // Perform initial search to display all data
  console.log("App initialized. Displaying initial data.");
}

// Event listeners
document.addEventListener('DOMContentLoaded', initializeApp);

// Attach event listeners to trigger search on explicit actions
searchButton.addEventListener('click', performSearch);
queryInput.addEventListener('keypress', (e) => { // Only search on Enter key
    if (e.key === 'Enter') {
        performSearch();
    }
});
sectionSelect.addEventListener('change', performSearch);
sourceSelect.addEventListener('change', performSearch);
resetButton.addEventListener('click', resetFilters);

// Export to PDF function (remains the same)
// Assuming you have a button with id 'exportPdfButton' in your index.html
if (exportPdfButton) {
    exportPdfButton.addEventListener('click', exportToPdf);
}
function exportToPdf() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsText = resultsContainer.innerText; // Get all text from results

    doc.setFontSize(12);
    doc.text("Cybersecurity Standards Search Results", 10, 10);
    doc.setFontSize(10);

    const splitText = doc.splitTextToSize(resultsText, 180); // 180mm width
    doc.text(splitText, 10, 20);
    doc.save("cybersecurity_standards_results.pdf");
}