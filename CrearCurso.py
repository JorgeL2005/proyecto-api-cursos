import json
import boto3
from datetime import datetime

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
course_table = dynamodb.Table('t_cursos')
tokens_table = dynamodb.Table('t_tokens_acceso')

def validate_token_admin(token):
    """
    Valida si el token es válido y si el usuario es administrador.
    """
    response = tokens_table.get_item(Key={'token': token})
    if 'Item' not in response:
        raise Exception('Token no encontrado o inválido')

    token_data = response['Item']
    expires = token_data['expires']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if now > expires:
        raise Exception('Token expirado')

    if token_data['role'] != 'admin':
        raise Exception('Acceso no autorizado. Solo los administradores pueden realizar esta acción.')

    return token_data

def lambda_handler(event, context):
    try:
        # Obtener token del encabezado
        headers = event.get('headers', {})
        token = headers.get('Authorization')
        if not token:
            raise Exception('Token de autorización no proporcionado.')

        # Validar token de administrador
        validate_token_admin(token)

        # Obtener datos del cuerpo de la solicitud
        if isinstance(event['body'], str):
            body = json.loads(event['body'])  # Decodificar JSON en diccionario
        else:
            body = event['body']

        tenant_id = body.get('tenant_id')
        curso_id = body.get('curso_id')
        course_name = body.get('CourseName')
        credits = body.get('Credits')
        description = body.get('Description')

        if not all([tenant_id, curso_id, course_name, credits, description]):
            raise Exception('Faltan campos requeridos: tenant_id, curso_id, CourseName, Credits, Description.')

        # Crear entrada para DynamoDB
        course_data = {
            'tenant_id': tenant_id,
            'curso_id': curso_id,
            'CourseName': course_name,
            'Credits': credits,
            'Description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        course_table.put_item(Item=course_data)

        return {
            'statusCode': 200,
            'body': {'message': 'Curso creado exitosamente.'}
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {'error': str(e)}
        }
