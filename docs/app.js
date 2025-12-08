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
        
        populateRegionFilter();
        initCustomDropdowns();
        filteredModels = [...allModels];
        renderModels();
        updateResultsCount();
        
        // Add event listeners
        document.getElementById('searchInput').addEventListener('input', filterModels);
    } catch (error) {
        console.error('Error loading models:', error);
        document.getElementById('modelsGrid').innerHTML = 
            '<p style="color: #c62828;">Error loading models data. Please try again.</p>';
    }
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
            matchesType = hasInferenceType(model, 'GLOBAL');
        } else if (selectedType === 'cris') {
            matchesType = hasCRIS(model);
        } else if (selectedType === 'on-demand') {
            matchesType = hasInferenceType(model, 'ON_DEMAND');
        } else if (selectedType === 'provisioned') {
            matchesType = hasInferenceType(model, 'PROVISIONED');
        }
        
        return matchesSearch && matchesRegion && matchesType;
    });
    
    renderModels();
    updateResultsCount();
}

function hasInferenceType(model, type) {
    return Object.values(model.inference_types).some(types => types.includes(type));
}

function hasCRIS(model) {
    const crisTypes = Object.keys(CRIS_REGIONS);
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
        
        return `
            <div class="model-card">
                <div class="model-header">
                    <div class="model-name">${model.id.split('.')[1] || model.id}</div>
                </div>
                
                <div class="model-badges">
                    <span class="badge ${badgeClass}">${provider}</span>
                    ${crisTypes.map(type => 
                        `<span class="badge badge-inference">${CRIS_REGIONS[type]}</span>`
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
