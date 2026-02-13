const fs = require('fs');

// Mock data and functions from app.js
const CRIS_REGIONS = {
    'GLOBAL': 'Global CRIS',
    'US': 'US CRIS',
    'EU': 'EU CRIS',
    'APAC': 'APAC CRIS',
    'JP': 'Japan CRIS',
    'AU': 'Australia CRIS',
    'CA': 'Canada CRIS'
};

function hasInferenceType(model, type, region) {
    if (region) {
        return model.inference_types[region]?.includes(type);
    }
    return Object.values(model.inference_types).some(types => types.includes(type));
}

function getInferenceTypes(model) {
    const types = new Set();
    Object.values(model.inference_types).forEach(typeList => {
        typeList.forEach(type => types.add(type));
    });
    return Array.from(types);
}

// Load data
const data = JSON.parse(fs.readFileSync('bedrock_models/bedrock_models.json', 'utf8'));
const allModels = Object.entries(data).map(([id, info]) => ({
    id,
    ...info
}));

// Test Case
const modelId = 'amazon.nova-canvas-v1:0';
const model = allModels.find(m => m.id === modelId);
const selectedRegion = 'ap-northeast-1';

console.log(`Testing model: ${modelId}`);
console.log(`Selected region: ${selectedRegion}`);

const inferenceTypes = getInferenceTypes(model);
console.log(`All inference types: ${inferenceTypes.join(', ')}`);

const crisTypes = inferenceTypes.filter(type => CRIS_REGIONS[type]);
const otherTypes = inferenceTypes.filter(type => !CRIS_REGIONS[type]);

console.log('--- Verification ---');

otherTypes.forEach(type => {
    const isSupported = hasInferenceType(model, type, selectedRegion);
    console.log(`Type: ${type}, Supported in ${selectedRegion}: ${isSupported}`);

    // Expected behavior
    if (type === 'PROVISIONED') {
        if (!isSupported) {
            console.log('✅ PASS: PROVISIONED is correctly identified as not supported in ap-northeast-1');
        } else {
            console.log('❌ FAIL: PROVISIONED should NOT be supported in ap-northeast-1');
        }
    } else if (type === 'ON_DEMAND') {
        if (isSupported) {
            console.log('✅ PASS: ON_DEMAND is correctly identified as supported in ap-northeast-1');
        } else {
            console.log('❌ FAIL: ON_DEMAND should be supported in ap-northeast-1');
        }
    }
});
