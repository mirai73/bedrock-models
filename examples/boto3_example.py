import boto3
from bedrock_models import Models, cris_model_id, global_model_id

br = boto3.client('bedrock-runtime')
print('Using', cris_model_id(Models.ANTHROPIC_CLAUDE_HAIKU_4_5_20251001))

resp = br.converse(modelId=global_model_id(Models.ANTHROPIC_CLAUDE_HAIKU_4_5_20251001),
    messages=[{'role':'user', 'content':[{'text':'Hello'}]}]
 )
print(resp)