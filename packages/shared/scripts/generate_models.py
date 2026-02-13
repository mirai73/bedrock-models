#!/usr/bin/env python3
"""
Script to generate model constants for both Python and TypeScript from bedrock_models.json.
"""

import json
import re
import os
from pathlib import Path

def model_id_to_field_name(model_id: str) -> str:
    """
    Convert a model ID to a constant name.
    """
    context_suffix = ''
    context_match = re.search(r':(\d+[kmg]|mm)$', model_id, re.IGNORECASE)
    if context_match:
        context_suffix = '_' + context_match.group(1).upper()
        model_id = model_id[:context_match.start()]
    
    name = re.sub(r'-v?\d+:\d+$', '', model_id)
    name = re.sub(r':\d+$', '', name)
    name = re.sub(r'-v\d+$', '', name)
    
    name = name.replace('.', '_').replace('-', '_')
    name = name.upper() + context_suffix
    
    return name

def collect_models(model_mapping):
    legacy_models = {}
    active_models = {}
    
    # Sort keys to ensure consistent selection of "latest" version if duplicates exist
    for model_id in sorted(model_mapping.keys()):
        model_data = model_mapping[model_id]
        lifecycle_status = model_data.get('model_lifecycle_status', 'ACTIVE')
        field_name = model_id_to_field_name(model_id)
        
        if lifecycle_status == 'LEGACY':
            # Use a dict to deduplicate by field name
            legacy_models[field_name] = model_id
        else:
            active_models[field_name] = model_id
            
    return active_models, legacy_models

def generate_python(active_models, legacy_models, output_file, stub_file):
    lines = [
        '"""',
        'Auto-generated class containing AWS Bedrock Foundation Model IDs.',
        '"""',
        '',
        'import warnings',
        'from .utils import cris_model_id, global_model_id',
        '',
        '',
        'class BedrockModel(str):',
        '    """Specialized string type that adds Bedrock-specific methods."""',
        '',
        '    def cris(self, region: str = None) -> str:',
        '        """Get the cross-region inference (CRIS) model ID for this model."""',
        '        return cris_model_id(str(self), region)',
        '',
        '    def global_cris(self, region: str = None) -> str:',
        '        """Get the global inference profile ID for this model."""',
        '        return global_model_id(str(self), region)',
        '',
        '',
        'class _DeprecatedModelDescriptor:',
        '    """Descriptor that emits deprecation warning when accessed."""',
        '    def __init__(self, model_id: str, message: str):',
        '        self.model_id = BedrockModel(model_id)',
        '        self.message = message',
        '    def __get__(self, obj, objtype=None):',
        '        warnings.warn(self.message, DeprecationWarning, stacklevel=2)',
        '        return self.model_id',
        '    def __set_name__(self, owner, name):',
        '        self.name = name',
        '',
        '',
        'class Models:',
        '    """Static class containing Bedrock foundation model IDs as constants."""',
        ''
    ]
    
    for field_name in sorted(active_models.keys()):
        lines.append(f'    {field_name} = BedrockModel("{active_models[field_name]}")')
    
    for field_name in sorted(legacy_models.keys()):
        model_id = legacy_models[field_name]
        msg = f"Model '{model_id}' has LEGACY status and may be removed by AWS. Consider migrating to a newer model."
        lines.append(f'    {field_name} = _DeprecatedModelDescriptor("{model_id}", "{msg}")')
        
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines) + '\n')
        
    stub_lines = [
        'from typing import Final, Optional',
        '',
        'class BedrockModel(str):',
        '    def cris(self, region: Optional[str] = None) -> str: ...',
        '    def global_cris(self, region: Optional[str] = None) -> str: ...',
        '',
        'class Models:',
        ''
    ]
    for field_name in sorted(active_models.keys()):
        stub_lines.append(f'    {field_name}: Final[BedrockModel]')
    for field_name in sorted(legacy_models.keys()):
        model_id = legacy_models[field_name]
        stub_lines.append(f'    {field_name}: Final[BedrockModel]  # deprecated: Model \'{model_id}\' has LEGACY status')
        
    with open(stub_file, 'w') as f:
        f.write('\n'.join(stub_lines) + '\n')

def generate_typescript(active_models, legacy_models, output_file):
    lines = [
        'import { crisModelId, globalModelId } from "./utils";',
        '',
        '/**',
        ' * Specialized string type that adds Bedrock-specific methods.',
        ' */',
        'export class BedrockModel extends String {',
        '  constructor(value: string) {',
        '    super(value);',
        '  }',
        '',
        '  /**',
        '   * Get the cross-region inference (CRIS) model ID for this model.',
        '   */',
        '  cris(region: string): string {',
        '    return crisModelId(this.toString(), region);',
        '  }',
        '',
        '  /**',
        '   * Get the global inference profile ID for this model.',
        '   */',
        '  global(region: string): string {',
        '    return globalModelId(this.toString(), region);',
        '  }',
        '}',
        '',
        'export const Models = {'
    ]
    
    # Combined sorted field names to maintain one sort order
    all_fields = sorted(set(active_models.keys()) | set(legacy_models.keys()))
    
    for field_name in all_fields:
        model_id = active_models.get(field_name) or legacy_models.get(field_name)
        lines.append(f"  {field_name}: new BedrockModel('{model_id}'),")
        
    lines.append('};')
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines) + '\n')

def main():
    # Base directory is the repo root
    root = Path(__file__).parent.parent.parent.parent
    json_path = root / 'packages/shared/bedrock_models.json'
    
    py_output = root / 'packages/python/bedrock_models/bedrock_model_ids.py'
    py_stub = root / 'packages/python/bedrock_models/bedrock_model_ids.pyi'
    ts_output = root / 'packages/typescript/src/models.ts'
    
    with open(json_path, 'r') as f:
        model_mapping = json.load(f)
        
    active_models, legacy_models = collect_models(model_mapping)
    
    print(f"Generating Python files...")
    generate_python(active_models, legacy_models, py_output, py_stub)
    
    print(f"Generating TypeScript file...")
    generate_typescript(active_models, legacy_models, ts_output)
    
    print("Done!")

if __name__ == '__main__':
    main()
