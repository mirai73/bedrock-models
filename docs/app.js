import { h, render } from 'https://esm.sh/preact@10.19.3';
import { useState, useEffect, useMemo, useRef } from 'https://esm.sh/preact@10.19.3/hooks';
import htm from 'https://esm.sh/htm@3.1.1';

const html = htm.bind(h);

const closeIcon = html`
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style=${{ display: 'block' }}>
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
`;

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
    'ap-east-2': { lat: 22.31, lng: 114.16, name: 'Hong Kong' },
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

// Global helper functions
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

function formatModelName(modelId) {
    const modelPart = modelId.split('.').slice(1).join('.') || modelId;
    const withoutVersion = modelPart.replace(/-v(\d+.*)$/, ' v$1');
    let formatted = withoutVersion.replace(/-/g, ' ').toUpperCase();
    formatted = formatted.replace(/(\d)\s+(\d)(?!\d|B)/g, '$1.$2');
    return formatted;
}

function getDaysAgoDateString(days) {
    const d = new Date();
    d.setDate(d.getDate() - days);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Subcomponents
function renderModalityIcons(model) {
    const modalityMap = { TEXT: 'T', IMAGE: 'I', VIDEO: 'V', AUDIO: 'A' };
    const input = (model.inputModalities || []).map(m => modalityMap[m] || m.charAt(0)).join('');
    const output = (model.outputModalities || []).map(m => modalityMap[m] || m.charAt(0)).join('');
    const streaming = model.responseStreamingSupported;
    const streamClass = streaming ? 'streaming' : '';
    const streamTitle = streaming ? 'Streaming supported' : 'Streaming not supported';

    return html`
        <span class="icon-badge" title=${`Input: ${(model.inputModalities || []).join(', ')}`}>${input}</span>
        <span class="icon-arrow">→</span>
        <span class="icon-badge ${streamClass}" title=${`Output: ${(model.outputModalities || []).join(', ')} (${streamTitle})`}>${output}</span>
    `;
}

function CustomSelect({ label, value, options, onSelect, isOpen, onToggle, showSearch, searchValue, onSearchChange, placeholder }) {
    const handleButtonClick = (e) => {
        e.stopPropagation();
        onToggle();
    };

    const selectedOption = options.find(opt => opt.value === value);
    const displayedLabel = selectedOption ? selectedOption.label : label;

    const filteredOptions = useMemo(() => {
        if (!showSearch || !searchValue) return options;
        const query = searchValue.toLowerCase();
        return options.filter(opt => opt.label.toLowerCase().includes(query));
    }, [options, showSearch, searchValue]);

    return html`
        <div class="custom-select ${isOpen ? 'open' : ''}">
            <button class="select-button" onClick=${handleButtonClick}>
                <span class="select-text">${displayedLabel}</span>
                <svg class="chevron-icon" width="12" height="8" viewBox="0 0 12 8" fill="none">
                    <path d="M1 1.5L6 6.5L11 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
            </button>
            <div class="select-dropdown" onClick=${e => e.stopPropagation()}>
                ${showSearch && html`
                    <div class="dropdown-search">
                        <input type="text" placeholder=${placeholder || 'Search...'} value=${searchValue} onInput=${onSearchChange} />
                    </div>
                `}
                <div class="dropdown-options">
                    ${filteredOptions.map(opt => html`
                        <div class="dropdown-option ${value === opt.value ? 'selected' : ''}" onClick=${() => onSelect(opt.value)}>
                            ${opt.label}
                        </div>
                    `)}
                </div>
            </div>
        </div>
    `;
}

function DateSelect({ value, customDate, onSelect, onCustomDateChange, isOpen, onToggle }) {
    const handleButtonClick = (e) => {
        e.stopPropagation();
        onToggle();
    };

    let displayLabel = 'Modified: All';
    if (value === '1') displayLabel = 'Modified: 1 Day';
    else if (value === '7') displayLabel = 'Modified: 7 Days';
    else if (value === '30') displayLabel = 'Modified: 30 Days';
    else if (value === 'custom') displayLabel = `Modified: ${customDate || 'Custom...'}`;

    return html`
        <div class="custom-select ${isOpen ? 'open' : ''}">
            <button class="select-button" onClick=${handleButtonClick}>
                <span class="select-text">${displayLabel}</span>
                <svg class="chevron-icon" width="12" height="8" viewBox="0 0 12 8" fill="none">
                    <path d="M1 1.5L6 6.5L11 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
            </button>
            <div class="select-dropdown" onClick=${e => e.stopPropagation()}>
                <div class="dropdown-options">
                    <div class="dropdown-option ${value === 'all' ? 'selected' : ''}" onClick=${() => onSelect('all')}>All</div>
                    <div class="dropdown-option ${value === '1' ? 'selected' : ''}" onClick=${() => onSelect('1')}>1 Day</div>
                    <div class="dropdown-option ${value === '7' ? 'selected' : ''}" onClick=${() => onSelect('7')}>7 Days</div>
                    <div class="dropdown-option ${value === '30' ? 'selected' : ''}" onClick=${() => onSelect('30')}>30 Days</div>
                    <div class="dropdown-option ${value === 'custom' ? 'selected' : ''}" onClick=${() => onSelect('custom')}>Custom...</div>
                </div>
                <div class="custom-date-picker-wrapper" style=${{ display: value === 'custom' ? 'block' : 'none', padding: '10px', borderTop: '1px solid var(--border-secondary)' }}>
                    <input type="date" class="date-input" value=${customDate} onChange=${e => onCustomDateChange(e.target.value)} />
                </div>
            </div>
        </div>
    `;
}

function MapModal({ activeMap, onClose, models, selectedRegion, crisProfileRegions }) {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const mapMarkersRef = useRef([]);

    const { modelId, modelName, crisType } = activeMap || {};

    useEffect(() => {
        if (!activeMap) {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
            return;
        }

        if (!mapInstanceRef.current && mapRef.current) {
            mapInstanceRef.current = L.map(mapRef.current, { maxZoom: 5 }).setView([20, 0], 2);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(mapInstanceRef.current);
        }

        const mapInstance = mapInstanceRef.current;
        if (!mapInstance) return;

        mapInstance.invalidateSize();

        mapMarkersRef.current.forEach(m => mapInstance.removeLayer(m));
        mapMarkersRef.current = [];

        let profileData = crisProfileRegions[crisType];
        if (!profileData) {
            mapInstance.setView([20, 0], 2);
            return;
        }

        const model = models.find(m => m.id === modelId);
        if (model) {
            if (Array.isArray(profileData)) {
                profileData = profileData.filter(region => hasInferenceType(model, crisType, region));
            } else {
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

        const addMarker = (regionCode, color, isSource = false) => {
            const location = REGION_LOCATIONS[regionCode];
            if (!location) return null;

            const marker = L.circleMarker([location.lat, location.lng], {
                radius: isSource ? 10 : 8,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(mapInstance);

            let popupContent = `<b>${location.name}</b><br>${regionCode}`;
            if (isSource && !isGlobal) {
                popupContent += `<br><span style="font-size:0.8em; color: #666;">Click to see coverage</span>`;
            }
            marker.bindPopup(popupContent);

            marker.bindTooltip(`<b>${location.name}</b><br>${regionCode}`, {
                permanent: false,
                direction: 'top'
            });

            if (isSource && !isGlobal) {
                marker.on('click', () => {
                    drawMapState(regionCode);
                });
            }

            mapMarkersRef.current.push(marker);
            bounds.extend([location.lat, location.lng]);
            return marker;
        };

        const drawMapState = (activeSource) => {
            mapMarkersRef.current.forEach(m => mapInstance.removeLayer(m));
            mapMarkersRef.current = [];
            const localBounds = L.latLngBounds();

            const sources = Object.keys(profileData);
            sources.forEach(source => {
                const isSelected = source === activeSource;
                const color = isSelected ? '#2196F3' : '#9E9E9E';

                const location = REGION_LOCATIONS[source];
                if (!location) return;

                const marker = L.circleMarker([location.lat, location.lng], {
                    radius: isSelected ? 10 : 8,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(mapInstance);

                let popupContent = `<b>${location.name}</b><br>${source} (Source)`;
                if (!isSelected) {
                    popupContent += `<br><span style="font-size:0.8em; color: #666;">Click to show coverage</span>`;
                }
                marker.bindPopup(popupContent);
                marker.bindTooltip(`<b>${location.name}</b><br>${source}`, { permanent: false, direction: 'top' });

                marker.on('click', () => {
                    drawMapState(source);
                });

                mapMarkersRef.current.push(marker);
                localBounds.extend([location.lat, location.lng]);
            });

            if (activeSource && profileData[activeSource]) {
                const targets = profileData[activeSource];
                targets.forEach(target => {
                    if (target === activeSource) return;

                    const location = REGION_LOCATIONS[target];
                    if (!location) return;

                    const marker = L.circleMarker([location.lat, location.lng], {
                        radius: 6,
                        fillColor: '#2196F3',
                        color: '#fff',
                        weight: 1,
                        opacity: 0.8,
                        fillOpacity: 0.6
                    }).addTo(mapInstance);

                    const isAlsoSource = !!profileData[target];
                    let popupContent = `<b>${location.name}</b><br>${target} (Target)`;
                    if (isAlsoSource) {
                        popupContent += `<br><span style="font-size:0.8em; color: #666;">Click to switch view</span>`;
                    }
                    marker.bindPopup(popupContent);
                    marker.bindTooltip(`<b>${location.name}</b><br>${target}`, { permanent: false, direction: 'top' });

                    if (isAlsoSource) {
                        marker.on('click', () => {
                            drawMapState(target);
                        });
                    }

                    mapMarkersRef.current.push(marker);
                    localBounds.extend([location.lat, location.lng]);
                });
            }

            if (mapMarkersRef.current.length > 0) {
                mapInstance.fitBounds(localBounds, { padding: [50, 50], maxZoom: 5 });
            }
        };

        if (isGlobal) {
            profileData.forEach(region => addMarker(region, '#2196F3'));
            if (mapMarkersRef.current.length > 0) {
                mapInstance.fitBounds(bounds, { padding: [50, 50], maxZoom: 5 });
            }
        } else {
            let initialSource = null;
            if (selectedRegion && profileData[selectedRegion]) {
                initialSource = selectedRegion;
            }
            drawMapState(initialSource);
        }

    }, [activeMap, models, selectedRegion, crisProfileRegions]);

    useEffect(() => {
        if (!activeMap) return;
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [activeMap]);

    if (!activeMap) return null;

    return html`
        <div id="mapModal" class="modal show" style=${{ display: 'flex' }} onClick=${(e) => e.target.id === 'mapModal' && onClose()}>
            <div class="modal-content">
                <span class="close-modal" onClick=${onClose} style=${{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px' }}>${closeIcon}</span>
                <h2>${modelName} - ${CRIS_REGIONS[crisType]} Regions</h2>
                <p class="modal-subtitle">Click on a source region to see the regions included in the profile</p>
                <div ref=${mapRef} id="map"></div>
            </div>
        </div>
    `;
}

function RegionsModal({ activeRegions, onClose, models }) {
    const { modelId, modelName } = activeRegions || {};
    
    useEffect(() => {
        if (!activeRegions) return;
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [activeRegions]);

    if (!activeRegions) return null;

    const model = models.find(m => m.id === modelId);
    if (!model) return null;

    const modelTypes = new Set();
    model.regions.forEach(r => {
        const types = model.inference_types[r] || [];
        types.forEach(t => modelTypes.add(t));
    });

    const hasGlobal = modelTypes.has('GLOBAL');
    const hasCris = Array.from(modelTypes).some(t => CRIS_REGIONS[t] && t !== 'GLOBAL');
    const hasOnDemand = modelTypes.has('ON_DEMAND');

    return html`
        <div id="regionsModal" class="modal show" style=${{ display: 'flex' }} onClick=${(e) => e.target.id === 'regionsModal' && onClose()}>
            <div class="modal-content">
                <span class="close-modal" onClick=${onClose} style=${{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px' }}>${closeIcon}</span>
                <h2>${modelName}</h2>
                
                <div class="legend-container modal-legend" style=${{ display: 'flex' }}>
                    ${hasGlobal && html`
                        <div class="legend-item">
                            <span class="inference-icon-small type-g">G</span>
                            <span>Global CRIS</span>
                        </div>
                    `}
                    ${hasCris && html`
                        <div class="legend-item">
                            <span class="inference-icon-small type-c">C</span>
                            <span>Region CRIS</span>
                        </div>
                    `}
                    ${hasOnDemand && html`
                        <div class="legend-item">
                            <span class="inference-icon-small type-r" title="In Region">R</span>
                            <span>In Region</span>
                        </div>
                    `}
                </div>

                <div class="modal-regions-list">
                    ${model.regions.map(region => {
                        const types = model.inference_types[region] || [];
                        const isGlobal = types.includes('GLOBAL');
                        const isCris = types.some(t => CRIS_REGIONS[t] && t !== 'GLOBAL');
                        const isOnDemand = types.includes('ON_DEMAND');

                        return html`
                            <div class="modal-region-item">
                                <div class="region-info">
                                    <span class="region-code">${region}</span>
                                    <span class="region-name">${REGION_LOCATIONS[region]?.name || ''}</span>
                                </div>
                                <div class="inference-icons-container">
                                    ${isGlobal && html`<span class="inference-icon-small type-g" title="Global CRIS">G</span>`}
                                    ${isCris && html`<span class="inference-icon-small type-c" title="Region CRIS">C</span>`}
                                    ${isOnDemand && html`<span class="inference-icon-small type-r" title="In Region">R</span>`}
                                </div>
                            </div>
                        `;
                    })}
                </div>
            </div>
        </div>
    `;
}

function ModelCard({ model, selectedRegion, onShowMap, onShowRegions, onCopy }) {
    const [expanded, setExpanded] = useState(false);

    const provider = getModelProvider(model.id);
    const badgeClass = getBadgeClass(model.id);
    const inferenceTypes = getInferenceTypes(model);
    const crisTypes = inferenceTypes.filter(type => CRIS_REGIONS[type]);
    const otherTypes = inferenceTypes.filter(type => !CRIS_REGIONS[type]);
    const formattedName = formatModelName(model.id);

    const handleCardClick = (e) => {
        if (window.innerWidth > 1024) return;
        if (e.target.closest('.copy-btn, .badge-interactive, .region-count-section')) return;
        setExpanded(!expanded);
    };

    const crisBadgesHtml = crisTypes.map(type => {
        const isDisabled = selectedRegion && !hasInferenceType(model, type, selectedRegion);
        return html`
            <span 
                class="badge badge-inference ${isDisabled ? 'badge-disabled' : 'badge-interactive'}" 
                title=${isDisabled ? 'Not available in selected region' : 'View Map'}
                onClick=${(e) => {
                    if (isDisabled) return;
                    e.stopPropagation();
                    onShowMap(type, model.id, formattedName);
                }}
            >
                ${CRIS_REGIONS[type]}
            </span>
        `;
    });

    const otherBadgesHtml = otherTypes.map(type => {
        const isDisabled = selectedRegion && !hasInferenceType(model, type, selectedRegion);
        return html`
            <span class="badge badge-inference ${isDisabled ? 'badge-disabled' : ''}" title=${isDisabled ? 'Not available in selected region' : ''}>
                ${type !== 'ON_DEMAND' ? type.replace('_', ' ') : 'In Region'}
            </span>
        `;
    });

    const statusBadge = html`
        <span class="badge ${model.model_lifecycle_status === 'ACTIVE' ? 'badge-active' : 'badge-legacy'}">
            ${model.model_lifecycle_status}
        </span>
    `;

    const apis = model.runtime_supported ? ['converse', 'invoke'] : [];
    const mantleApis = model.mantle_apis || [];
    const apiBadgesHtml = [
        ...apis.map(api => html`<span class="badge badge-api-runtime">${api}</span>`),
        ...mantleApis.map(api => html`<span class="badge badge-api">${api}</span>`)
    ];

    const copyBtn = html`
        <button class="copy-btn" onClick=${(e) => { e.stopPropagation(); onCopy(model.id); }} title="Copy model ID">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M10.5 2H3.5C2.67157 2 2 2.67157 2 3.5V10.5C2 11.3284 2.67157 12 3.5 12H10.5C11.3284 12 12 11.3284 12 10.5V3.5C12 2.67157 11.3284 2 10.5 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 5.5V12.5C14 13.3284 13.3284 14 12.5 14H5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </button>
    `;

    const chevronSvg = html`
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M6 4L10 8L6 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `;

    const modalityIcons = renderModalityIcons(model);

    return html`
        <div class="model-card ${model.model_lifecycle_status === 'LEGACY' ? 'legacy' : ''} ${expanded ? 'expanded' : ''}" onClick=${handleCardClick}>
            <!-- Mobile compact view -->
            <div class="mobile-compact">
                <div class="model-name">${formattedName}</div>
                <div class="model-capabilities">${modalityIcons}</div>
                <span class="mobile-expand-arrow">${chevronSvg}</span>
            </div>
            
            <!-- Mobile expanded details -->
            <div class="mobile-details">
                <div style=${{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <span class="badge ${badgeClass}">${provider}</span>
                    ${statusBadge}
                </div>
                <div class="model-badges">${crisBadgesHtml}${otherBadgesHtml}</div>
                <div class="model-badges model-api-badges">${apiBadgesHtml}</div>
                <div class="model-id">
                    <span>${model.id}</span>
                    ${copyBtn}
                </div>
                <div class="model-section region-count-section" onClick=${(e) => { e.stopPropagation(); onShowRegions(model.id, formattedName); }} title="View all regions">
                    <div class="section-title">
                        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style=${{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }}>
                            <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        <span>${model.regions.length} region${model.regions.length !== 1 ? 's' : ''}</span>
                        <span class="info-hint"> (tap to view)</span>
                    </div>
                </div>
                <div class="model-meta-row">
                    <span class="model-meta-label">Last Modified</span>
                    <span class="model-meta-value">${model.lastChanged}</span>
                </div>
            </div>

            <!-- Desktop view -->
            <div class="model-header">
                <div class="model-name">${formattedName}</div>
                <span class="badge ${badgeClass}">${provider}</span>
            </div>
            <div class="model-capabilities">${modalityIcons}</div>
            <div class="model-badges">
                ${crisBadgesHtml}${otherBadgesHtml}
                ${statusBadge}
            </div>
            <div class="model-badges model-api-badges">${apiBadgesHtml}</div>
            <div class="model-id">
                <span>${model.id}</span>
                ${copyBtn}
            </div>
            <div class="model-section region-count-section" onClick=${(e) => { e.stopPropagation(); onShowRegions(model.id, formattedName); }} title="View all regions">
                <div class="section-title">
                    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" style=${{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }}>
                        <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                    <span>${model.regions.length} region${model.regions.length !== 1 ? 's' : ''}</span>
                    <span class="info-hint"> (tap to view)</span>
                </div>
            </div>
            <div class="model-meta-row">
                <span class="model-meta-label">Last Modified</span>
                <span class="model-meta-value">${model.lastChanged}</span>
            </div>
        </div>
    `;
}

function ModelTable({ models, selectedRegion, onShowMap, onShowRegions, onCopy }) {
    if (models.length === 0) {
        return html`
            <div class="models-table-wrapper">
                <table class="models-table">
                    <thead>
                        <tr>
                            <th>Model Name</th>
                            <th>Provider</th>
                            <th>Capabilities</th>
                            <th>Inference</th>
                            <th>APIs</th>
                            <th>Status</th>
                            <th>Last Modified</th>
                            <th>Regions</th>
                            <th>Model ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="9" style=${{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                                No models found matching your criteria.
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    return html`
        <div class="models-table-wrapper">
            <table class="models-table">
                <thead>
                    <tr>
                        <th>Model Name</th>
                        <th>Provider</th>
                        <th>Capabilities</th>
                        <th>Inference</th>
                        <th>APIs</th>
                        <th>Status</th>
                        <th>Last Modified</th>
                        <th>Regions</th>
                        <th>Model ID</th>
                    </tr>
                </thead>
                <tbody>
                    ${models.map(model => {
                        const provider = getModelProvider(model.id);
                        const badgeClass = getBadgeClass(model.id);
                        const inferenceTypes = getInferenceTypes(model);
                        const crisTypes = inferenceTypes.filter(type => CRIS_REGIONS[type]);
                        const otherTypes = inferenceTypes.filter(type => !CRIS_REGIONS[type]);
                        const formattedName = formatModelName(model.id);
                        const modalityIcons = renderModalityIcons(model);

                        const statusClass = model.model_lifecycle_status === 'ACTIVE' ? 'badge-active' : 'badge-legacy';
                        const apis = model.runtime_supported ? ['converse', 'invoke'] : [];
                        const mantleApis = model.mantle_apis || [];
                        const apiBadgesHtml = [
                            ...apis.map(api => html`<span class="badge badge-api-runtime">${api}</span>`),
                            ...mantleApis.map(api => html`<span class="badge badge-api">${api}</span>`)
                        ];

                        return html`
                            <tr>
                                <td class="table-model-name">${formattedName}</td>
                                <td><span class="badge ${badgeClass}">${provider}</span></td>
                                <td class="table-capabilities">${modalityIcons}</td>
                                <td>
                                    <div class="table-inference">
                                        ${crisTypes.map(type => {
                                            const isDisabled = selectedRegion && !hasInferenceType(model, type, selectedRegion);
                                            return html`
                                                <span 
                                                    class="badge badge-inference ${isDisabled ? 'badge-disabled' : 'badge-interactive'}" 
                                                    title=${isDisabled ? 'Not available in selected region' : 'View Map'}
                                                    onClick=${() => {
                                                        if (isDisabled) return;
                                                        onShowMap(type, model.id, formattedName);
                                                    }}
                                                >
                                                    ${CRIS_REGIONS[type]}
                                                </span>
                                            `;
                                        })}
                                        ${otherTypes.map(type => {
                                            const isDisabled = selectedRegion && !hasInferenceType(model, type, selectedRegion);
                                            return html`
                                                <span class="badge badge-inference ${isDisabled ? 'badge-disabled' : ''}" title=${isDisabled ? 'Not available in selected region' : ''}>
                                                    ${type !== 'ON_DEMAND' ? type.replace('_', ' ') : 'In Region'}
                                                </span>
                                            `;
                                        })}
                                    </div>
                                </td>
                                <td class="table-apis">${apiBadgesHtml}</td>
                                <td><span class="badge ${statusClass}">${model.model_lifecycle_status}</span></td>
                                <td class="table-last-modified">${model.lastChanged}</td>
                                <td>
                                    <span class="table-region-count" onClick=${() => onShowRegions(model.id, formattedName)} title="View all regions">
                                        ${model.regions.length} region${model.regions.length !== 1 ? 's' : ''}
                                    </span>
                                </td>
                                <td class="table-model-id">
                                    <code>${model.id}</code>
                                    <button class="copy-btn" onClick=${() => onCopy(model.id)} title="Copy model ID">
                                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                            <path d="M10.5 2H3.5C2.67157 2 2 2.67157 2 3.5V10.5C2 11.3284 2.67157 12 3.5 12H10.5C11.3284 12 12 11.3284 12 10.5V3.5C12 2.67157 11.3284 2 10.5 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                            <path d="M14 5.5V12.5C14 13.3284 13.3284 14 12.5 14H5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                    </button>
                                </td>
                            </tr>
                        `;
                    })}
                </tbody>
            </table>
        </div>
    `;
}

function App() {
    const [models, setModels] = useState([]);
    const [metadata, setMetadata] = useState({});
    const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');
    const [viewMode, setViewMode] = useState(() => localStorage.getItem('viewMode') || 'grid');
    const [toastMessage, setToastMessage] = useState(null);

    // Filter states
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedRegion, setSelectedRegion] = useState('');
    const [selectedType, setSelectedType] = useState('');
    const [selectedDateFilter, setSelectedDateFilter] = useState('all');
    const [selectedCustomDate, setSelectedCustomDate] = useState('');
    const [selectedApiFilter, setSelectedApiFilter] = useState('all');

    // UI state
    const [openDropdown, setOpenDropdown] = useState(null);
    const [regionQuery, setRegionQuery] = useState('');
    const [activeMapModal, setActiveMapModal] = useState(null);
    const [activeRegionsModal, setActiveRegionsModal] = useState(null);
    const [errorMsg, setErrorMsg] = useState(null);

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    useEffect(() => {
        async function loadData() {
            const timestamp = Date.now();
            let rawData, rawMetadata = {};
            try {
                const response = await fetch(`https://raw.githubusercontent.com/mirai73/bedrock-models/main/packages/shared/bedrock_models.json?t=${timestamp}`);
                rawData = await response.json();
                
                try {
                    const metaResponse = await fetch(`https://raw.githubusercontent.com/mirai73/bedrock-models/main/packages/shared/bedrock_models_metadata.json?t=${timestamp}`);
                    rawMetadata = await metaResponse.json();
                } catch (metaErr) {
                    console.error('Could not load github raw metadata:', metaErr);
                }
            } catch (err) {
                console.warn('Could not load from GitHub raw, falling back to local files:', err);
                try {
                    const response = await fetch(`./bedrock_models.json?t=${timestamp}`);
                    rawData = await response.json();
                    
                    try {
                        const metaResponse = await fetch(`./bedrock_models_metadata.json?t=${timestamp}`);
                        rawMetadata = await metaResponse.json();
                    } catch (metaErr) {
                        console.error('Could not load local metadata:', metaErr);
                    }
                } catch (localErr) {
                    console.error('Error loading local fallback data:', localErr);
                    setErrorMsg('Error loading models data. Please try again.');
                    return;
                }
            }

            const parsedModels = Object.entries(rawData).map(([id, info]) => {
                const modelMeta = rawMetadata[id] || {};
                return {
                    id,
                    ...info,
                    lastChanged: modelMeta.last_changed || 'N/A'
                };
            });

            setModels(parsedModels);
            setMetadata(rawMetadata);
        }

        loadData();
    }, []);

    useEffect(() => {
        const handleOutsideClick = () => {
            setOpenDropdown(null);
        };
        document.addEventListener('click', handleOutsideClick);
        return () => document.removeEventListener('click', handleOutsideClick);
    }, []);

    const handleViewModeChange = (mode) => {
        setViewMode(mode);
        localStorage.setItem('viewMode', mode);
    };

    const handleThemeToggle = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
    };

    const crisProfileRegions = useMemo(() => {
        const regionSets = {};
        models.forEach(model => {
            if (model.inferenceProfile) {
                Object.entries(model.inferenceProfile).forEach(([profile, data]) => {
                    if (Array.isArray(data)) {
                        if (!regionSets[profile]) regionSets[profile] = new Set();
                        data.forEach(r => regionSets[profile].add(r));
                    } else {
                        if (!regionSets[profile]) regionSets[profile] = {};
                        Object.entries(data).forEach(([source, targets]) => {
                            if (!regionSets[profile][source]) regionSets[profile][source] = new Set();
                            targets.forEach(t => regionSets[profile][source].add(t));
                        });
                    }
                });
            }
        });

        const result = {};
        Object.entries(regionSets).forEach(([profile, data]) => {
            if (data instanceof Set) {
                result[profile] = Array.from(data).sort();
            } else {
                result[profile] = {};
                Object.entries(data).forEach(([source, targetSet]) => {
                    result[profile][source] = Array.from(targetSet).sort();
                });
            }
        });
        return result;
    }, [models]);

    const sortedRegions = useMemo(() => {
        const regions = new Set();
        models.forEach(model => {
            model.regions.forEach(r => regions.add(r));
        });
        return Array.from(regions).sort();
    }, [models]);

    const globalLastUpdated = useMemo(() => {
        const dates = Object.values(metadata)
            .map(m => m.last_changed)
            .filter(d => d && d !== 'N/A');
        return dates.length > 0 ? dates.reduce((max, d) => d > max ? d : max, dates[0]) : 'N/A';
    }, [metadata]);

    const filteredModels = useMemo(() => {
        const query = searchTerm.toLowerCase();
        return models.filter(model => {
            const matchesSearch = model.id.toLowerCase().includes(query);
            const matchesRegion = !selectedRegion || model.regions.includes(selectedRegion);

            let matchesType = true;
            if (selectedType === 'global-cris') {
                matchesType = hasInferenceType(model, 'GLOBAL', selectedRegion);
            } else if (selectedType === 'cris') {
                matchesType = hasCRIS(model, selectedRegion);
            } else if (selectedType === 'on-demand') {
                matchesType = hasInferenceType(model, 'ON_DEMAND', selectedRegion);
            } else if (selectedType === 'mantle') {
                matchesType = model.mantle_supported_regions && model.mantle_supported_regions.length > 0 && (!selectedRegion || model.mantle_supported_regions.includes(selectedRegion));
            }

            let matchesDate = true;
            if (selectedDateFilter && selectedDateFilter !== 'all') {
                let filterDateStr = '';
                if (selectedDateFilter === 'custom') {
                    filterDateStr = selectedCustomDate;
                } else {
                    const days = parseInt(selectedDateFilter, 10);
                    if (!isNaN(days)) {
                        filterDateStr = getDaysAgoDateString(days);
                    }
                }
                if (filterDateStr) {
                    matchesDate = model.lastChanged && model.lastChanged !== 'N/A' && model.lastChanged >= filterDateStr;
                }
            }

            let matchesApi = true;
            if (selectedApiFilter === 'runtime') {
                matchesApi = !!model.runtime_supported;
            } else if (selectedApiFilter === 'mantle') {
                matchesApi = model.mantle_apis && model.mantle_apis.length > 0;
            }

            return matchesSearch && matchesRegion && matchesType && matchesDate && matchesApi;
        });
    }, [models, searchTerm, selectedRegion, selectedType, selectedDateFilter, selectedCustomDate, selectedApiFilter]);

    const handleCopy = (text) => {
        navigator.clipboard.writeText(text).then(() => {
            setToastMessage(`Copied: ${text}`);
            setTimeout(() => {
                setToastMessage(null);
            }, 2000);
        });
    };

    const handleToggleDropdown = (name) => {
        setOpenDropdown(openDropdown === name ? null : name);
    };

    const [isMobile, setIsMobile] = useState(window.innerWidth <= 1024);
    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth <= 1024);
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const isTableView = viewMode === 'table' && !isMobile;

    if (errorMsg) {
        return html`
            <div class="container">
                <header>
                    <h1 class="main-title">Amazon Bedrock Models</h1>
                </header>
                <p style=${{ color: '#c62828', textAlign: 'center', padding: '40px' }}>${errorMsg}</p>
            </div>
        `;
    }

    return html`
        <div class="container">
            <header>
                <div class="header-top">
                    <h1 class="main-title">Amazon Bedrock Models</h1>
                    <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme" onClick=${handleThemeToggle}>
                        <svg class="sun-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" style=${{ display: theme === 'dark' ? 'block' : 'none' }}>
                            <circle cx="10" cy="10" r="4" stroke="currentColor" stroke-width="1.5" />
                            <path d="M10 2V4M10 16V18M18 10H16M4 10H2M15.5 4.5L14 6M6 14L4.5 15.5M15.5 15.5L14 14M6 6L4.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                        </svg>
                        <svg class="moon-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" style=${{ display: theme === 'light' ? 'block' : 'none' }}>
                            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>
                    </button>
                </div>
                <p class="subtitle">
                    Explore the available foundation models in Amazon Bedrock. Click on the CRIS badges to see the regions included in the profile.
                    <span class="last-updated-wrapper" style=${{ display: 'block', marginTop: '6px', fontSize: '0.85em', opacity: 0.75 }}>
                        Last updated: <span id="lastUpdatedDate">${globalLastUpdated}</span>
                    </span>
                </p>
            </header>

            <div class="legend">
                <span class="legend-title">Capabilities:</span>
                <span class="legend-item"><span class="icon-badge">T</span> Text</span>
                <span class="legend-item"><span class="icon-badge">I</span> Image</span>
                <span class="legend-item"><span class="icon-badge">V</span> Video</span>
                <span class="legend-item"><span class="icon-badge">A</span> Audio</span>
                <span class="legend-item"><span class="icon-badge streaming">Orange</span> = Streaming</span>
            </div>

            <div class="controls">
                <div class="search-box">
                    <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M7 12C9.76142 12 12 9.76142 12 7C12 4.23858 9.76142 2 7 2C4.23858 2 2 4.23858 2 7C2 9.76142 4.23858 12 7 12Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                        <path d="M14 14L10.5 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    <input type="text" id="searchInput" placeholder="Search models..." value=${searchTerm} onInput=${e => setSearchTerm(e.target.value)} />
                </div>

                <div class="view-toggle" id="viewToggle">
                    <button class="view-toggle-btn ${viewMode === 'grid' ? 'active' : ''}" onClick=${() => handleViewModeChange('grid')} title="Card view">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
                            <rect x="9" y="1" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
                            <rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
                            <rect x="9" y="9" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                    </button>
                    <button class="view-toggle-btn ${viewMode === 'table' ? 'active' : ''}" onClick=${() => handleViewModeChange('table')} title="Table view">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M1 3H15M1 8H15M1 13H15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                    </button>
                </div>

                <div class="filters">
                    <${CustomSelect}
                        label="All Regions"
                        value=${selectedRegion}
                        isOpen=${openDropdown === 'region'}
                        onToggle=${() => handleToggleDropdown('region')}
                        onSelect=${val => { setSelectedRegion(val); setOpenDropdown(null); setRegionQuery(''); }}
                        showSearch=${true}
                        searchValue=${regionQuery}
                        onSearchChange=${e => setRegionQuery(e.target.value)}
                        placeholder="Search regions..."
                        options=${[
                            { value: '', label: 'All Regions' },
                            ...sortedRegions.map(r => ({ value: r, label: r }))
                        ]}
                    />

                    <${CustomSelect}
                        label="All Types"
                        value=${selectedType}
                        isOpen=${openDropdown === 'type'}
                        onToggle=${() => handleToggleDropdown('type')}
                        onSelect=${val => { setSelectedType(val); setOpenDropdown(null); }}
                        options=${[
                            { value: '', label: 'All Types' },
                            { value: 'global-cris', label: 'Global CRIS' },
                            { value: 'cris', label: 'CRIS (Any)' },
                            { value: 'on-demand', label: 'In Region' },
                            { value: 'mantle', label: 'Mantle Supported' }
                        ]}
                    />

                    <${CustomSelect}
                        label="All APIs"
                        value=${selectedApiFilter}
                        isOpen=${openDropdown === 'api'}
                        onToggle=${() => handleToggleDropdown('api')}
                        onSelect=${val => { setSelectedApiFilter(val); setOpenDropdown(null); }}
                        options=${[
                            { value: 'all', label: 'All APIs' },
                            { value: 'runtime', label: 'Runtime API' },
                            { value: 'mantle', label: 'Mantle API' }
                        ]}
                    />

                    <${DateSelect}
                        value=${selectedDateFilter}
                        customDate=${selectedCustomDate}
                        isOpen=${openDropdown === 'date'}
                        onToggle=${() => handleToggleDropdown('date')}
                        onSelect=${val => {
                            if (val !== 'custom') {
                                setSelectedDateFilter(val);
                                setSelectedCustomDate('');
                                setOpenDropdown(null);
                            } else {
                                setSelectedDateFilter('custom');
                            }
                        }}
                        onCustomDateChange=${val => {
                            setSelectedCustomDate(val);
                            setSelectedDateFilter('custom');
                            setOpenDropdown(null);
                        }}
                    />
                </div>
            </div>

            <div class="results-info">
                <span id="resultsCount">Showing ${filteredModels.length} of ${models.length} models</span>
            </div>

            ${isTableView ? html`
                <${ModelTable}
                    models=${filteredModels}
                    selectedRegion=${selectedRegion}
                    onShowMap=${(crisType, modelId, modelName) => setActiveMapModal({ crisType, modelId, modelName })}
                    onShowRegions=${(modelId, modelName) => setActiveRegionsModal({ modelId, modelName })}
                    onCopy=${handleCopy}
                />
            ` : html`
                <div id="modelsGrid" class="models-grid">
                    ${filteredModels.length === 0 ? html`
                        <p style=${{ color: '#666', gridColumn: '1/-1', textAlign: 'center', padding: '40px' }}>
                            No models found matching your criteria.
                        </p>
                    ` : filteredModels.map(model => html`
                        <${ModelCard}
                            key=${model.id}
                            model=${model}
                            selectedRegion=${selectedRegion}
                            onShowMap=${(crisType, modelId, modelName) => setActiveMapModal({ crisType, modelId, modelName })}
                            onShowRegions=${(modelId, modelName) => setActiveRegionsModal({ modelId, modelName })}
                            onCopy=${handleCopy}
                        />
                    `)}
                </div>
            `}

            <!-- Map Modal -->
            <${MapModal}
                activeMap=${activeMapModal}
                onClose=${() => setActiveMapModal(null)}
                models=${models}
                selectedRegion=${selectedRegion}
                crisProfileRegions=${crisProfileRegions}
            />

            <!-- Regions List Modal -->
            <${RegionsModal}
                activeRegions=${activeRegionsModal}
                onClose=${() => setActiveRegionsModal(null)}
                models=${models}
            />

            <!-- Toast Notification -->
            <div id="toast" class="toast ${toastMessage ? 'show' : ''}">${toastMessage}</div>
        </div>
    `;
}

// Mount the App
render(html`<${App} />`, document.getElementById('app'));
