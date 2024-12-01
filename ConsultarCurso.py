import json
import boto3
from datetime import datetime

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
course_table = dynamodb.Table('t_cursos')
tokens_table = dynamodb.Table('t_tokens_acceso')

def validate_token(token):
    """
    Valida si el token es válido.
    """
    response = tokens_table.get_item(Key={'token': token})
    if 'Item' not in response:
        raise Exception('Token no encontrado o inválido')

    token_data = response['Item']
    expires = token_data['expires']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if now > expires:
        raise Exception('Token expirado')

    return token_data

def lambda_handler(event, context):
    try:
        # Obtener token del encabezado
        headers = event.get('headers', {})
        token = headers.get('Authorization')
        if not token:
            raise Exception('Token de autorización no proporcionado.')

        # Validar token
        validate_token(token)

        # Obtener datos del cuerpo de la solicitud
        if isinstance(event['body'], str):
            body = json.loads(event['body'])  # Decodificar JSON en diccionario
        else:
            body = event['body']

        tenant_id = body.get('tenant_id')
        curso_id = body.get('curso_id')
        if not all([tenant_id, curso_id]):
            raise Exception('Faltan parámetros requeridos: tenant_id y curso_id.')

        # Consultar el curso en DynamoDB
        response = course_table.get_item(
            Key={
                'tenant_id': tenant_id,
                'curso_id': curso_id
            }
        )

        if 'Item' not in response:
            raise Exception('Curso no encontrado.')

        program_data = response['Item']
        
        return {
            'statusCode': 200,
            'body': program_data
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {'error': str(e)}
        }
