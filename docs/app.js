let allModels = [];
let filteredModels = [];

// CRIS regions mapping
const CRIS_REGIONS = {
    'GLOBAL': 'Global CRIS',
    'US': 'US CRIS',
    'EU': 'EU CRIS',
    'APAC': 'APAC CRIS',
    'JP': 'Japan CRIS',
    'AU': 'Australia CRIS',
    'CA': 'Canada CRIS'
};

// Region locations (lat, lng)
const REGION_LOCATIONS = {
    'us-east-1': { lat: 38.03, lng: -78.51, name: 'N. Virginia' },
    'us-east-2': { lat: 40.42, lng: -82.91, name: 'Ohio' },
    'us-west-1': { lat: 37.77, lng: -122.41, name: 'N. California' },
    'us-west-2': { lat: 45.52, lng: -122.68, name: 'Oregon' },
    'ca-central-1': { lat: 45.50, lng: -73.56, name: 'Montreal' },
    'ca-west-1': { lat: 51.04, lng: -114.07, name: 'Calgary' },
    'sa-east-1': { lat: -23.55, lng: -46.63, name: 'São Paulo' },
    'eu-central-1': { lat: 50.11, lng: 8.68, name: 'Frankfurt' },
    'eu-central-2': { lat: 47.37, lng: 8.54, name: 'Zurich' },
    'eu-north-1': { lat: 59.33, lng: 18.06, name: 'Stockholm' },
    'eu-south-1': { lat: 45.46, lng: 9.19, name: 'Milan' },
    'eu-south-2': { lat: 40.41, lng: -3.70, name: 'Spain' },
    'eu-west-1': { lat: 53.35, lng: -6.26, name: 'Dublin' },
    'eu-west-2': { lat: 51.50, lng: -0.12, name: 'London' },
    'eu-west-3': { lat: 48.86, lng: 2.35, name: 'Paris' },
    'il-central-1': { lat: 32.08, lng: 34.78, name: 'Tel Aviv' },
    'me-central-1': { lat: 25.27, lng: 55.30, name: 'UAE' },
    'af-south-1': { lat: -33.92, lng: 18.42, name: 'Cape Town' },
    'ap-east-1': { lat: 22.31, lng: 114.16, name: 'Hong Kong' },
    'ap-east-2': { lat: 22.31, lng: 114.16, name: 'Hong Kong' }, // Often maps to Hong Kong
    'ap-northeast-1': { lat: 35.68, lng: 139.76, name: 'Tokyo' },
    'ap-northeast-2': { lat: 37.56, lng: 126.97, name: 'Seoul' },
    'ap-northeast-3': { lat: 34.69, lng: 135.50, name: 'Osaka' },
    'ap-south-1': { lat: 19.07, lng: 72.87, name: 'Mumbai' },
    'ap-south-2': { lat: 17.38, lng: 78.48, name: 'Hyderabad' },
    'ap-southeast-1': { lat: 1.35, lng: 103.82, name: 'Singapore' },
    'ap-southeast-2': { lat: -33.87, lng: 151.21, name: 'Sydney' },
    'ap-southeast-3': { lat: -6.20, lng: 106.84, name: 'Jakarta' },
    'ap-southeast-4': { lat: -37.81, lng: 144.96, name: 'Melbourne' },
    'ap-southeast-5': { lat: 3.13, lng: 101.68, name: 'Malaysia' },
    'ap-southeast-7': { lat: 13.75, lng: 100.50, name: 'Thailand' }
};

// CRIS Profile underlying regions (dynamically populated)
let CRIS_PROFILE_REGIONS = {};

let map = null;
let mapMarkers = [];

// Theme management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const themeToggle = document.getElementById('themeToggle');
    themeToggle.addEventListener('click', toggleTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Custom dropdown state
let selectedRegion = '';
let selectedType = '';

// Load and initialize
async function init() {
    initTheme();
    try {
        const response = await fetch('bedrock_models.json');
        const data = await response.json();

        allModels = Object.entries(data).map(([id, info]) => ({
            id,
            ...info
        }));

        populateCrisRegions();
        populateRegionFilter();
        initCustomDropdowns();
        filteredModels = [...allModels];
        renderModels();
        updateResultsCount();

        // Add event listeners
        document.getElementById('searchInput').addEventListener('input', filterModels);

        // Modal close listeners
        document.querySelector('.close-modal').addEventListener('click', closeMapModal);
        document.getElementById('mapModal').addEventListener('click', (e) => {
            if (e.target.id === 'mapModal') closeMapModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeMapModal();
        });

    } catch (error) {
        console.error('Error loading models:', error);
        document.getElementById('modelsGrid').innerHTML =
            '<p style="color: #c62828;">Error loading models data. Please try again.</p>';
    }
}

function initMap() {
    if (map) return;

    // Initialize map centered on world
    map = L.map('map').setView([20, 0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

function showRegionMap(crisType, modelName) {
    const modal = document.getElementById('mapModal');
    const title = document.getElementById('modalTitle');

    title.textContent = `${modelName} - ${CRIS_REGIONS[crisType]} Regions`;
    modal.classList.add('show');
    modal.style.display = 'flex'; // Ensure display is flex for centering

    // Need to wait for modal to be visible before sizing map
    setTimeout(() => {
        initMap();
        map.invalidateSize();

        // Clear existing markers
        mapMarkers.forEach(marker => map.removeLayer(marker));
        mapMarkers = [];

        const regions = CRIS_PROFILE_REGIONS[crisType] || [];
        const bounds = L.latLngBounds();

        regions.forEach(regionCode => {
            const location = REGION_LOCATIONS[regionCode];
            if (location) {
                const marker = L.marker([location.lat, location.lng])
                    .bindPopup(`<b>${location.name}</b><br>${regionCode}`)
                    .addTo(map);
                mapMarkers.push(marker);
                bounds.extend([location.lat, location.lng]);
            }
        });

        if (regions.length > 0) {
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 5 });
        } else {
            map.setView([20, 0], 2);
        }
    }, 100);
}

function closeMapModal() {
    const modal = document.getElementById('mapModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

function populateCrisRegions() {
    const regionSets = {};

    allModels.forEach(model => {
        if (model.inferenceProfile) {
            Object.entries(model.inferenceProfile).forEach(([profile, regions]) => {
                if (!regionSets[profile]) {
                    regionSets[profile] = new Set();
                }
                regions.forEach(region => regionSets[profile].add(region));
            });
        }
    });

    // Convert Sets to Arrays
    CRIS_PROFILE_REGIONS = {};
    Object.entries(regionSets).forEach(([profile, set]) => {
        CRIS_PROFILE_REGIONS[profile] = Array.from(set).sort();
    });

    console.log('Populated CRIS Regions:', CRIS_PROFILE_REGIONS);
}

function populateRegionFilter() {
    const regions = new Set();
    allModels.forEach(model => {
        model.regions.forEach(region => regions.add(region));
    });

    const regionOptions = document.getElementById('regionOptions');
    const sortedRegions = Array.from(regions).sort();

    // Add "All Regions" option
    const allOption = document.createElement('div');
    allOption.className = 'dropdown-option selected';
    allOption.dataset.value = '';
    allOption.textContent = 'All Regions';
    regionOptions.appendChild(allOption);

    // Add region options
    sortedRegions.forEach(region => {
        const option = document.createElement('div');
        option.className = 'dropdown-option';
        option.dataset.value = region;
        option.textContent = region;
        regionOptions.appendChild(option);
    });
}

function initCustomDropdowns() {
    // Region dropdown
    const regionContainer = document.getElementById('regionFilterContainer');
    const regionButton = document.getElementById('regionButton');
    const regionDropdown = document.getElementById('regionDropdown');
    const regionOptions = document.getElementById('regionOptions');
    const regionSearch = document.getElementById('regionSearch');

    regionButton.addEventListener('click', (e) => {
        e.stopPropagation();
        regionContainer.classList.toggle('open');
        document.getElementById('typeFilterContainer').classList.remove('open');
        if (regionContainer.classList.contains('open')) {
            regionSearch.focus();
        }
    });

    regionSearch.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const options = regionOptions.querySelectorAll('.dropdown-option');
        options.forEach(option => {
            const text = option.textContent.toLowerCase();
            option.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    });

    regionOptions.addEventListener('click', (e) => {
        if (e.target.classList.contains('dropdown-option')) {
            selectedRegion = e.target.dataset.value;
            regionButton.querySelector('.select-text').textContent = e.target.textContent;

            // Update selected state
            regionOptions.querySelectorAll('.dropdown-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            e.target.classList.add('selected');

            regionContainer.classList.remove('open');
            regionSearch.value = '';
            regionOptions.querySelectorAll('.dropdown-option').forEach(opt => {
                opt.style.display = 'block';
            });
            filterModels();
        }
    });

    // Type dropdown
    const typeContainer = document.getElementById('typeFilterContainer');
    const typeButton = document.getElementById('typeButton');
    const typeDropdown = document.getElementById('typeDropdown');
    const typeOptions = document.getElementById('typeOptions');

    typeButton.addEventListener('click', (e) => {
        e.stopPropagation();
        typeContainer.classList.toggle('open');
        regionContainer.classList.remove('open');
    });

    typeOptions.addEventListener('click', (e) => {
        if (e.target.classList.contains('dropdown-option')) {
            selectedType = e.target.dataset.value;
            typeButton.querySelector('.select-text').textContent = e.target.textContent;

            // Update selected state
            typeOptions.querySelectorAll('.dropdown-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            e.target.classList.add('selected');

            typeContainer.classList.remove('open');
            filterModels();
        }
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', () => {
        regionContainer.classList.remove('open');
        typeContainer.classList.remove('open');
    });

    // Prevent dropdown from closing when clicking inside
    regionDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    typeDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

function filterModels() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    filteredModels = allModels.filter(model => {
        // Search filter
        const matchesSearch = model.id.toLowerCase().includes(searchTerm);

        // Region filter
        const matchesRegion = !selectedRegion || model.regions.includes(selectedRegion);

        // Type filter
        let matchesType = true;
        if (selectedType === 'global-cris') {
            matchesType = hasInferenceType(model, 'GLOBAL', selectedRegion);
        } else if (selectedType === 'cris') {
            matchesType = hasCRIS(model, selectedRegion);
        } else if (selectedType === 'on-demand') {
            matchesType = hasInferenceType(model, 'ON_DEMAND', selectedRegion);
        }

        return matchesSearch && matchesRegion && matchesType;
    });

    renderModels();
    updateResultsCount();
}

function hasInferenceType(model, type, region) {
    if (region) {
        return model.inference_types[region]?.includes(type);
    }
    return Object.values(model.inference_types).some(types => types.includes(type));
}

function hasCRIS(model, region) {
    const crisTypes = Object.keys(CRIS_REGIONS);
    if (region) {
        const typesAtRegion = model.inference_types[region];
        return typesAtRegion?.some(type => crisTypes.includes(type));
    }
    return Object.values(model.inference_types).some(types =>
        types.some(type => crisTypes.includes(type))
    );
}

function getModelProvider(modelId) {
    const provider = modelId.split('.')[0];
    return provider.charAt(0).toUpperCase() + provider.slice(1);
}

function getBadgeClass(modelId) {
    const provider = modelId.split('.')[0].toLowerCase();
    const badgeMap = {
        'anthropic': 'badge-anthropic',
        'amazon': 'badge-amazon',
        'ai21': 'badge-ai21',
        'cohere': 'badge-cohere',
        'meta': 'badge-meta',
        'mistral': 'badge-mistral',
        'stability': 'badge-stability'
    };
    return badgeMap[provider] || 'badge-default';
}

function getInferenceTypes(model) {
    const types = new Set();
    Object.values(model.inference_types).forEach(typeList => {
        typeList.forEach(type => types.add(type));
    });
    return Array.from(types);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Could add a toast notification here
        console.log('Copied:', text);
    });
}

function formatModelName(modelId) {
    // Get the part after the provider (e.g., "nova-2-sonic-v1:0" from "amazon.nova-2-sonic-v1:0")
    const modelPart = modelId.split('.')[1] || modelId;

    // Remove the version suffix (everything after the last hyphen followed by 'v')
    // e.g., "nova-2-sonic-v1:0" -> "nova-2-sonic"
    const withoutVersion = modelPart.replace(/-v\d+.*$/, '');

    // Replace hyphens with spaces and convert to uppercase
    let formatted = withoutVersion.replace(/-/g, ' ').toUpperCase();

    // Replace space between a digit and a single digit (not followed by more digits or B) with a period
    // e.g., "LLAMA3 3" -> "LLAMA3.3", "LLAMA3 2 1B" -> "LLAMA3.2 1B"
    // but "LLAMA3 8B" stays "LLAMA3 8B", "GEMMA 3 27B" stays "GEMMA 3 27B"
    formatted = formatted.replace(/(\d)\s+(\d)(?!\d|B)/g, '$1.$2');

    return formatted;
}

function renderModels() {
    const grid = document.getElementById('modelsGrid');

    if (filteredModels.length === 0) {
        grid.innerHTML = '<p style="color: #666; grid-column: 1/-1; text-align: center; padding: 40px;">No models found matching your criteria.</p>';
        return;
    }

    grid.innerHTML = filteredModels.map(model => {
        const provider = getModelProvider(model.id);
        const badgeClass = getBadgeClass(model.id);
        const inferenceTypes = getInferenceTypes(model);
        const crisTypes = inferenceTypes.filter(type => CRIS_REGIONS[type]);
        const otherTypes = inferenceTypes.filter(type => !CRIS_REGIONS[type]);

        const displayRegions = model.regions.slice(0, 3);
        const moreRegions = model.regions.length - 3;
        const formattedName = formatModelName(model.id);

        return `
            <div class="model-card">
                <div class="model-header">
                    <div class="model-name">${formattedName}</div>
                </div>
                
                <div class="model-badges">
                    <span class="badge ${badgeClass}">${provider}</span>
                    ${crisTypes.map(type =>
            `<span class="badge badge-inference badge-interactive" onclick="showRegionMap('${type}', '${formattedName}')" title="View Map">${CRIS_REGIONS[type]}</span>`
        ).join('')}
                    ${otherTypes.map(type =>
            `<span class="badge badge-inference">${type.replace('_', ' ')}</span>`
        ).join('')}
                    <span class="badge ${model.model_lifecycle_status === 'ACTIVE' ? 'badge-active' : 'badge-legacy'}">
                        ${model.model_lifecycle_status}
                    </span>
                </div>
                
                <div class="model-id">
                    <span>${model.id}</span>
                    <button class="copy-btn" onclick="copyToClipboard('${model.id}')" title="Copy model ID">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M10.5 2H3.5C2.67157 2 2 2.67157 2 3.5V10.5C2 11.3284 2.67157 12 3.5 12H10.5C11.3284 12 12 11.3284 12 10.5V3.5C12 2.67157 11.3284 2 10.5 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M14 5.5V12.5C14 13.3284 13.3284 14 12.5 14H5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
                
                <div class="model-section">
                    <div class="section-title">Available Regions</div>
                    <div class="regions-list">
                        ${displayRegions.map(region =>
            `<span class="region-tag">${region}</span>`
        ).join('')}
                        ${moreRegions > 0 ? `<span class="region-more">+${moreRegions} more</span>` : ''}
                    </div>
                </div>
                
                <div class="model-section">
                    <div class="section-title">
                        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style="display: inline; vertical-align: middle; margin-right: 4px;">
                            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        ${model.regions.length} region${model.regions.length !== 1 ? 's' : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function updateResultsCount() {
    const count = document.getElementById('resultsCount');
    count.textContent = `Showing ${filteredModels.length} of ${allModels.length} models`;
}

// Initialize on load
init();
