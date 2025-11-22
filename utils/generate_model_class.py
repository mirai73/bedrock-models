#!/usr/bin/env python3
"""
Script to generate a Python class with static fields from bedrock_models.json.
Each field name is the model name (capitalized, with underscores, without trailing version codes).
Each field value is the model ID.
"""

import json
import re


def model_id_to_field_name(model_id: str) -> str:
    """
    Convert a model ID to a Python field name.
    - Remove version information (e.g., -v1:0, -v2:0, -1:0) but keep context sizes
    - Replace dots, hyphens, and colons with underscores
    - Capitalize
    
    Examples:
        'anthropic.claude-3-sonnet-20240229-v1:0' -> 'ANTHROPIC_CLAUDE_3_SONNET_20240229'
        'amazon.titan-text-express-v1' -> 'AMAZON_TITAN_TEXT_EXPRESS'
        'amazon.nova-lite-v1:0:24k' -> 'AMAZON_NOVA_LITE_24K'
        'openai.gpt-oss-120b-1:0' -> 'OPENAI_GPT_OSS_120B'
    """
    # First, extract any context size suffix (like :24k, :300k, :mm)
    context_suffix = ''
    context_match = re.search(r':(\d+[kmg]|mm)$', model_id, re.IGNORECASE)
    if context_match:
        context_suffix = '_' + context_match.group(1).upper()
        model_id = model_id[:context_match.start()]
    
    # Remove version patterns like -v1:0, -v2:0, -1:0, -0:1, :0, :1
    name = re.sub(r'-v?\d+:\d+$', '', model_id)
    name = re.sub(r':\d+$', '', name)
    name = re.sub(r'-v\d+$', '', name)
    
    # Replace dots and hyphens with underscores
    name = name.replace('.', '_').replace('-', '_')
    
    # Capitalize and add context suffix
    name = name.upper() + context_suffix
    
    return name


def generate_class_file(
    json_file: str = 'bedrock_models/bedrock_models.json',
    output_file: str = 'bedrock_models/bedrock_model_ids.py',
    stub_file: str = 'bedrock_models/bedrock_model_ids.pyi'
):
    """
    Read the JSON file and generate a Python class file with static fields.
    
    Args:
        json_file: Path to the input JSON file
        output_file: Path to the output Python file
        stub_file: Path to the output type stub file for IDE support
    """
    # Read the JSON file
    with open(json_file, 'r') as f:
        model_mapping = json.load(f)
    
    # Separate legacy and active models
    legacy_models = {}
    active_models = {}
    
    for model_id, model_data in model_mapping.items():
        lifecycle_status = model_data.get('model_lifecycle_status', 'ACTIVE')
        field_name = model_id_to_field_name(model_id)
        
        if lifecycle_status == 'LEGACY':
            legacy_models[field_name] = model_id
        else:
            active_models[field_name] = model_id
    
    # Generate the class content
    lines = [
        '"""',
        'Auto-generated class containing AWS Bedrock Foundation Model IDs.',
        'Generated from bedrock_models.json',
        '"""',
        '',
        'import warnings',
        '',
        '',
        'class _DeprecatedModelDescriptor:',
        '    """Descriptor that emits deprecation warning when accessed."""',
        '    ',
        '    def __init__(self, model_id: str, message: str):',
        '        self.model_id = model_id',
        '        self.message = message',
        '    ',
        '    def __get__(self, obj, objtype=None):',
        '        warnings.warn(self.message, DeprecationWarning, stacklevel=2)',
        '        return self.model_id',
        '    ',
        '    def __set_name__(self, owner, name):',
        '        self.name = name',
        '',
        '',
        'class Models:',
        '    """Static class containing Bedrock foundation model IDs as constants."""',
        ''
    ]
    
    # Add active models
    for field_name in sorted(active_models.keys()):
        lines.append(f'    {field_name} = "{active_models[field_name]}"')
    
    # Add legacy models with descriptor
    for field_name in sorted(legacy_models.keys()):
        model_id = legacy_models[field_name]
        msg = f"Model '{model_id}' has LEGACY status and may be removed by AWS. Consider migrating to a newer model."
        lines.append(f'    {field_name} = _DeprecatedModelDescriptor("{model_id}", "{msg}")')
    
    # Write to output file
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
        f.write('\n')
    
    # Generate type stub file for IDE support
    # For LEGACY models, we add special comments that IDEs can parse
    stub_lines = [
        '"""',
        'Type stub file for bedrock_model_ids.py',
        'Provides IDE support and type hints for Bedrock model IDs.',
        '"""',
        '',
        'from typing import Final',
        '',
        '',
        'class Models:',
        '    """Static class containing Bedrock foundation model IDs as constants."""',
        ''
    ]
    
    # Add active models
    for field_name in sorted(active_models.keys()):
        stub_lines.append(f'    {field_name}: Final[str]')
    
    # Add legacy models with deprecation comments
    # IDEs parse these special comment formats
    for field_name in sorted(legacy_models.keys()):
        model_id = legacy_models[field_name]
        stub_lines.append(f'    {field_name}: Final[str]  # deprecated: Model \'{model_id}\' has LEGACY status')
    
    # Write stub file
    with open(stub_file, 'w') as f:
        f.write('\n'.join(stub_lines))
        f.write('\n')
    
    print(f"Generated {output_file} with {len(model_mapping)} model constants")
    print(f"  - {len(legacy_models)} LEGACY models with deprecation warnings")
    print(f"  - {len(active_models)} ACTIVE models")
    print(f"Generated {stub_file} for IDE support")


def main():
    """Main function to generate the model class file."""
    generate_class_file()


if __name__ == '__main__':
    main()
