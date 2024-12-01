import json
import boto3
from datetime import datetime
from decimal import Decimal

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

def decimal_to_standard(obj):
    """
    Convierte objetos Decimal en tipos estándar de Python.
    """
    if isinstance(obj, Decimal):
        if obj % 1 == 0:  # Si es un número entero
            return int(obj)
        else:  # Si es un número decimal
            return float(obj)
    if isinstance(obj, list):
        return [decimal_to_standard(i) for i in obj]
    if isinstance(obj, dict):
        return {k: decimal_to_standard(v) for k, v in obj.items()}
    return obj

def lambda_handler(event, context):
    try:
        # Obtener token del encabezado
        headers = event.get('headers', {})
        token = headers.get('Authorization')
        if not token:
            raise Exception('Token de autorización no proporcionado.')

        # Validar token
        token_data = validate_token(token)
        tenant_id = token_data.get('tenant_id')
        if not tenant_id:
            raise Exception('No se pudo determinar el tenant_id del token.')

        # Escanear todos los cursos
        response = course_table.scan(
            FilterExpression="tenant_id = :tenant OR tenant_id = :global",
            ExpressionAttributeValues={
                ":tenant": tenant_id,
                ":global": "global"
            }
        )
        cursos = response.get('Items', [])

        # Convertir objetos Decimal a tipos estándar
        cursos = [decimal_to_standard(curso) for curso in cursos]

        if not cursos:
            return {
                'statusCode': 404,
                'body': {'error': 'No se encontraron cursos.'}
            }

        # Retornar directamente el JSON como un diccionario
        return {
            'statusCode': 200,
            'body': {'cursos': cursos}
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {'error': str(e)}
        }
