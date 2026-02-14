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
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                closeMapModal();
                closeRegionsModal();
            });
        });

        document.getElementById('mapModal').addEventListener('click', (e) => {
            if (e.target.id === 'mapModal') closeMapModal();
        });

        document.getElementById('regionsModal').addEventListener('click', (e) => {
            if (e.target.id === 'regionsModal') closeRegionsModal();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeMapModal();
                closeRegionsModal();
            }
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
    map = L.map('map', { maxZoom: 5 }).setView([20, 0], 2);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}


// CRIS Profile underlying regions (dynamically populated)
// Structure: 
// For GLOBAL: ["region1", "region2"]
// For others: { "source_region1": ["target1", "target2"], ... }

function showRegionMap(crisType, modelId, modelName) {
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

        let profileData = CRIS_PROFILE_REGIONS[crisType];

        if (!profileData) {
            map.setView([20, 0], 2);
            return;
        }

        // Filter profileData based on model availability logic from hasInferenceType
        const model = allModels.find(m => m.id === modelId);
        if (model) {
            if (Array.isArray(profileData)) {
                // Global: Filter the array of regions
                profileData = profileData.filter(region => hasInferenceType(model, crisType, region));
            } else {
                // Regional: Filter the keys (sources) of the object
                const filteredData = {};
                Object.keys(profileData).forEach(source => {
                    if (hasInferenceType(model, crisType, source)) {
                        filteredData[source] = profileData[source];
                    }
                });
                profileData = filteredData;
            }
        }


        const isGlobal = Array.isArray(profileData);
        const bounds = L.latLngBounds();

        // Helper to add marker
        const addMarker = (regionCode, color, isSource = false, sourceFor = null) => {
            const location = REGION_LOCATIONS[regionCode];
            if (!location) return null;

            const marker = L.circleMarker([location.lat, location.lng], {
                radius: 8,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);

            let popupContent = `<b>${location.name}</b><br>${regionCode}`;
            if (isSource && !isGlobal) {
                popupContent += `<br><span style="font-size:0.8em; color: #666;">Click to see coverage</span>`;
            }
            marker.bindPopup(popupContent);

            // Add tooltip for hover
            marker.bindTooltip(`<b>${location.name}</b><br>${regionCode}`, {
                permanent: false,
                direction: 'top'
            });

            // Interaction for non-global source regions
            if (isSource && !isGlobal && sourceFor) {
                marker.on('click', () => {
                    // Reset all markers to default state first
                    updateMapState(profileData, regionCode);
                });
            }

            mapMarkers.push(marker);
            bounds.extend([location.lat, location.lng]);
            return marker;
        };

        // Render Initial State
        if (isGlobal) {
            // GLOBAL: Just show all regions as Blue
            profileData.forEach(region => addMarker(region, '#2196F3'));
        } else {
            // Regional: Check for selected region filter
            let initialSource = null;
            if (selectedRegion && profileData[selectedRegion]) {
                initialSource = selectedRegion;
            }

            updateMapState(profileData, initialSource);
        }

        if (mapMarkers.length > 0) {
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 5 });
        } else {
            map.setView([20, 0], 2);
        }
    }, 100);
}

function updateMapState(profileData, activeSource) {
    // Clear existing markers to redraw (simplest approach for state change)
    mapMarkers.forEach(marker => map.removeLayer(marker));
    mapMarkers = [];
    const bounds = L.latLngBounds();

    const sources = Object.keys(profileData);

    // 1. Draw all sources first (z-index lower ideally, but map order matters)
    sources.forEach(source => {
        const isSelected = source === activeSource;
        const color = isSelected ? '#2196F3' : '#9E9E9E'; // Blue if selected, Grey otherwise

        const location = REGION_LOCATIONS[source];
        if (!location) return;

        const marker = L.circleMarker([location.lat, location.lng], {
            radius: isSelected ? 10 : 8,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);

        let popupContent = `<b>${location.name}</b><br>${source} (Source)`;
        if (!isSelected) {
            popupContent += `<br><span style="font-size:0.8em; color: #666;">Click to show coverage</span>`;
        }
        marker.bindPopup(popupContent);

        marker.bindTooltip(`<b>${location.name}</b><br>${source}`, {
            permanent: false,
            direction: 'top'
        });

        marker.on('click', () => {
            updateMapState(profileData, source);
        });

        mapMarkers.push(marker);
        bounds.extend([location.lat, location.lng]);
    });

    // 2. If a source is active, draw its targets
    if (activeSource && profileData[activeSource]) {
        const targets = profileData[activeSource];
        targets.forEach(target => {
            if (target === activeSource) return; // Already drawn as source

            const location = REGION_LOCATIONS[target];
            if (!location) return;

            const marker = L.circleMarker([location.lat, location.lng], {
                radius: 6,
                fillColor: '#2196F3', // Blue for targets
                color: '#fff',
                weight: 1,
                opacity: 0.8,
                fillOpacity: 0.6
            }).addTo(map);

            // Check if this target is also a valid source
            const isAlsoSource = !!profileData[target];

            let popupContent = `<b>${location.name}</b><br>${target} (Target)`;
            if (isAlsoSource) {
                popupContent += `<br><span style="font-size:0.8em; color: #666;">Click to switch view</span>`;
            }
            marker.bindPopup(popupContent);

            marker.bindTooltip(`<b>${location.name}</b><br>${target}`, {
                permanent: false,
                direction: 'top'
            });

            if (isAlsoSource) {
                marker.on('click', () => {
                    updateMapState(profileData, target);
                });
            }

            mapMarkers.push(marker);
            bounds.extend([location.lat, location.lng]);
        });

        // Draw lines from source to targets? Optional but cool. 
        // Keeping it simple for now as per plan: just highlight markers.
    }

    if (mapMarkers.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 5 });
    }
}

function closeMapModal() {
    const modal = document.getElementById('mapModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

function showAllRegions(modelId, modelName) {
    const model = allModels.find(m => m.id === modelId);
    if (!model) return;

    const modal = document.getElementById('regionsModal');
    const title = document.getElementById('regionsModalTitle');
    const container = document.getElementById('regionsListContainer');

    title.textContent = modelName;

    // Detect which types are present for this model across all its regions
    const modelTypes = new Set();
    model.regions.forEach(r => {
        const types = model.inference_types[r] || [];
        types.forEach(t => modelTypes.add(t));
    });

    const hasGlobal = modelTypes.has('GLOBAL');
    const hasCris = Array.from(modelTypes).some(t => CRIS_REGIONS[t] && t !== 'GLOBAL');
    const hasOnDemand = modelTypes.has('ON_DEMAND');

    // Add legend under the title
    let legend = document.getElementById('modalLegend');
    if (!legend) {
        legend = document.createElement('div');
        legend.id = 'modalLegend';
        legend.className = 'legend-container modal-legend';
        title.after(legend);
    }

    let legendHtml = '';
    if (hasGlobal) legendHtml += `
        <div class="legend-item">
            <span class="inference-icon-small type-g">G</span>
            <span>Global CRIS</span>
        </div>`;
    if (hasCris) legendHtml += `
        <div class="legend-item">
            <span class="inference-icon-small type-c">C</span>
            <span>Region CRIS</span>
        </div>`;
    if (hasOnDemand) legendHtml += `
        <div class="legend-item">
            <span class="inference-icon-small type-r" title="In Region">R</span>
            <span>In Region</span>
        </div>`;

    legend.innerHTML = legendHtml;
    legend.style.display = legendHtml ? 'flex' : 'none';

    container.innerHTML = model.regions.map(region => {
        const types = model.inference_types[region] || [];
        const isGlobal = types.includes('GLOBAL');
        const isCris = types.some(t => CRIS_REGIONS[t] && t !== 'GLOBAL');
        const isOnDemand = types.includes('ON_DEMAND');

        return `
            <div class="modal-region-item">
                <div class="region-info">
                    <span class="region-code">${region}</span>
                    <span class="region-name">${REGION_LOCATIONS[region]?.name || ''}</span>
                </div>
                <div class="inference-icons-container">
                    ${isGlobal ? '<span class="inference-icon-small type-g" title="Global CRIS">G</span>' : ''}
                    ${isCris ? '<span class="inference-icon-small type-c" title="Region CRIS">C</span>' : ''}
                    ${isOnDemand ? '<span class="inference-icon-small type-r" title="In Region">R</span>' : ''}
                </div>
            </div>
        `;
    }).join('');

    modal.classList.add('show');
    modal.style.display = 'flex';
}

function closeRegionsModal() {
    const modal = document.getElementById('regionsModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

function populateCrisRegions() {
    const regionSets = {};

    allModels.forEach(model => {
        if (model.inferenceProfile) {
            Object.entries(model.inferenceProfile).forEach(([profile, data]) => {
                if (Array.isArray(data)) {
                    // GLOBAL: List of regions
                    if (!regionSets[profile]) {
                        regionSets[profile] = new Set(); // Use Set for unique list
                    }
                    // For GLOBAL, we just store the list of regions
                    data.forEach(r => regionSets[profile].add(r));
                } else {
                    // Regional: Dict of Source -> Targets
                    // We need to merge this structure.
                    // If multiple models have "US" profile, we merge their source maps.
                    if (!regionSets[profile]) {
                        regionSets[profile] = {}; // Object for source maps
                    }

                    Object.entries(data).forEach(([source, targets]) => {
                        if (!regionSets[profile][source]) {
                            regionSets[profile][source] = new Set();
                        }
                        targets.forEach(t => regionSets[profile][source].add(t));
                    });
                }
            });
        }
    });

    // Convert Sets to Arrays for final structure
    CRIS_PROFILE_REGIONS = {};
    Object.entries(regionSets).forEach(([profile, data]) => {
        if (data instanceof Set) {
            // Global
            CRIS_PROFILE_REGIONS[profile] = Array.from(data).sort();
        } else {
            // Regional
            CRIS_PROFILE_REGIONS[profile] = {};
            Object.entries(data).forEach(([source, targetSet]) => {
                CRIS_PROFILE_REGIONS[profile][source] = Array.from(targetSet).sort();
            });
        }
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

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2000);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(`Copied: ${text}`);
    });
}

function formatModelName(modelId) {
    // Get the part after the provider (e.g., "nova-2-sonic-v1:0" from "amazon.nova-2-sonic-v1:0")
    const modelPart = modelId.split('.').slice(1).join('.') || modelId;

    // Remove the version suffix (everything after the last hyphen followed by 'v')
    // e.g., "nova-2-sonic-v1:0" -> "nova-2-sonic"
    const withoutVersion = modelPart.replace(/-v(\d+.*)$/, ' v$1');

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
        const formattedName = formatModelName(model.id);

        return `
            <div class="model-card">
                <div class="model-header">
                    <div class="model-name">${formattedName}</div>
                    <button class="copy-btn mobile-only" onclick="copyToClipboard('${model.id}')" title="Copy model ID">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M10.5 2H3.5C2.67157 2 2 2.67157 2 3.5V10.5C2 11.3284 2.67157 12 3.5 12H10.5C11.3284 12 12 11.3284 12 10.5V3.5C12 2.67157 11.3284 2 10.5 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M14 5.5V12.5C14 13.3284 13.3284 14 12.5 14H5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
                
                <div class="model-badges">
                    <span class="badge ${badgeClass}">${provider}</span>
                    ${crisTypes.map(type => {
            const isDisabled = selectedRegion && !hasInferenceType(model, type, selectedRegion);
            const disabledClass = isDisabled ? 'badge-disabled' : '';
            const clickHandler = isDisabled ? '' : `onclick="showRegionMap('${type}', '${model.id}', '${formattedName}')"`;
            const interactiveClass = isDisabled ? '' : 'badge-interactive';
            const titleAttr = isDisabled ? 'title="Not available in selected region"' : 'title="View Map"';

            return `<span class="badge badge-inference ${interactiveClass} ${disabledClass}" ${clickHandler} ${titleAttr}>${CRIS_REGIONS[type]}</span>`;
        }).join('')}
                    ${otherTypes.map(type => {
            const isDisabled = selectedRegion && !hasInferenceType(model, type, selectedRegion);
            const disabledClass = isDisabled ? 'badge-disabled' : '';
            const titleAttr = isDisabled ? 'title="Not available in selected region"' : '';
            return `<span class="badge badge-inference ${disabledClass}" ${titleAttr}>${type !== 'ON_DEMAND' ? type.replace('_', ' ') : 'In Region'}</span>`;
        }).join('')}
                    <span class="badge ${model.model_lifecycle_status === 'ACTIVE' ? 'badge-active' : 'badge-legacy'}">
                        ${model.model_lifecycle_status}
                    </span>
                </div>
                
                <div class="model-id desktop-only">
                    <span>${model.id}</span>
                    <button class="copy-btn" onclick="copyToClipboard('${model.id}')" title="Copy model ID">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M10.5 2H3.5C2.67157 2 2 2.67157 2 3.5V10.5C2 11.3284 2.67157 12 3.5 12H10.5C11.3284 12 12 11.3284 12 10.5V3.5C12 2.67157 11.3284 2 10.5 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M14 5.5V12.5C14 13.3284 13.3284 14 12.5 14H5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
                
                
                <div class="model-section region-count-section" onclick="showAllRegions('${model.id}', '${formattedName}')" title="View all regions">
                    <div class="section-title">
                        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style="display: inline; vertical-align: middle; margin-right: 4px;">
                            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        <span>${model.regions.length} region${model.regions.length !== 1 ? 's' : ''}</span>
                        <span class="info-hint"> (tap to view)</span>
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
