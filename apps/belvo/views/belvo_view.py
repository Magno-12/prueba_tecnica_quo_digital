import requests

from base64 import b64encode
from django.conf import settings

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.belvo.utils.credential import TEST_CREDENTIALS


class BelvoAPIViewSet(viewsets.GenericViewSet):
    """
    ViewSet para interactuar con la API de Belvo mediante requests HTTP directos.
    Maneja la obtención de instituciones bancarias, cuentas y transacciones.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Este método es requerido por Swagger para generar la documentación.
        """
        if getattr(self, 'swagger_fake_view', False):
            return []
        return []

    def get_headers(self):
        """
        Retorna los headers necesarios para la API de Belvo usando Basic Auth
        Siguiendo el estándar de Basic Authentication
        """
        auth_string = f"{settings.BELVO_SECRET_ID}:{settings.BELVO_SECRET_PASSWORD}"
        auth_base64 = b64encode(auth_string.encode()).decode()
        
        return {
            'Authorization': f'Basic {auth_base64}',  # Formato correcto de Basic Auth
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    @swagger_auto_schema(
        operation_description="Lista las instituciones bancarias disponibles",
        responses={
            200: openapi.Response(
                description="Lista de instituciones bancarias",
                examples={
                    "application/json": {
                        "count": "integer",
                        "next": "string or null",
                        "previous": "string or null",
                        "results": [{
                            "id": "integer",
                            "name": "string",
                            "display_name": "string",
                            "country_codes": ["string"],
                            "type": "string",
                            "logo": "string"
                        }]
                    }
                }
            ),
            400: "Error en la solicitud",
            401: "Error de autenticación"
        }
    )
    @action(detail=False, methods=['get'])
    def institutions(self, request):
        """
        Obtiene la lista de instituciones bancarias disponibles.
        """
        try:
            response = requests.get(
                f'{settings.BELVO_API_URL}institutions/',
                headers=self.get_headers()
            )
            print("Response:", response.text)  # Debug
            print("Headers:", response.request.headers)  # Debug
            response.raise_for_status()
            data = response.json()

            institutions = [{
                'id': inst['id'],
                'name': inst['name'],
                'display_name': inst['display_name'],
                'type': inst['type'],
                'logo': inst.get('logo', ''),
                'icon_logo': inst.get('icon_logo', ''),
                'text_logo': inst.get('text_logo', ''),
                'country_codes': inst['country_codes'],
                'website': inst.get('website', '')
            } for inst in data['results']]

            return Response({
                'count': data['count'],
                'next': data.get('next'),
                'previous': data.get('previous'),
                'results': institutions
            })
        except requests.exceptions.RequestException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Lista las cuentas asociadas a un link",
        manual_parameters=[
            openapi.Parameter(
                'link_id',
                openapi.IN_QUERY,
                description="ID del link de Belvo",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Lista de cuentas",
                examples={
                    "application/json": {
                        "count": "integer",
                        "results": [{
                            "id": "string",
                            "link": "string",
                            "name": "string",
                            "category": "string",
                            "balance": {
                                "current": "number",
                                "available": "number"
                            },
                            "currency": "string",
                            "institution": {
                                "name": "string",
                                "type": "string"
                            }
                        }]
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def accounts(self, request):
        """
        Lista las cuentas bancarias asociadas a un link.
        """
        try:
            link_id = request.query_params.get('link_id')
            if not link_id:
                return Response(
                    {'error': 'Se requiere el link_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            response = requests.get(
                f'{settings.BELVO_API_URL}accounts/',
                headers=self.get_headers(),
                params={'link': link_id}
            )
            response.raise_for_status()
            data = response.json()

            accounts = [{
                'id': acc['id'],
                'link': acc['link'],
                'name': acc['name'],
                'category': acc['category'],
                'type': acc.get('type'),
                'balance': acc['balance'],
                'currency': acc['currency'],
                'institution': acc['institution']
            } for acc in data['results']]

            return Response({
                'count': data['count'],
                'results': accounts
            })
        except requests.exceptions.RequestException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Lista transacciones y calcula el balance",
        manual_parameters=[
            openapi.Parameter(
                'link_id',
                openapi.IN_QUERY,
                description="ID del link de Belvo",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'account_id',
                openapi.IN_QUERY,
                description="ID de la cuenta",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'date_from',
                openapi.IN_QUERY,
                description="Fecha inicial (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'date_to',
                openapi.IN_QUERY,
                description="Fecha final (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Transacciones y KPI de balance",
                examples={
                    "application/json": {
                        "kpi": {
                            "income": "number",
                            "expenses": "number",
                            "balance": "number"
                        },
                        "transactions": [{
                            "id": "string",
                            "amount": "number",
                            "type": "string",
                            "category": "string",
                            "description": "string",
                            "merchant": "object",
                            "transacted_at": "string",
                            "status": "string"
                        }]
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """
        Obtiene transacciones y calcula el KPI de balance.
        """
        try:
            params = {
                'link': request.query_params.get('link_id'),
                'account': request.query_params.get('account_id'),
                'date_from': request.query_params.get('date_from'),
                'date_to': request.query_params.get('date_to')
            }

            if not all(params.values()):
                return Response(
                    {'error': 'Todos los parámetros son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            response = requests.get(
                f'{settings.BELVO_API_URL}transactions/',
                headers=self.get_headers(),
                params=params
            )
            response.raise_for_status()
            data = response.json()

            # Calcular KPI
            transactions = data['results']
            income = sum(t['amount'] for t in transactions if t['type'] == 'INFLOW')
            expenses = sum(t['amount'] for t in transactions if t['type'] == 'OUTFLOW')
            balance = income - expenses

            formatted_transactions = [{
                'id': t['id'],
                'amount': t['amount'],
                'type': t['type'],
                'category': t['category'],
                'description': t['description'],
                'merchant': t.get('merchant', {}),
                'transacted_at': t['transacted_at'],
                'status': t['status']
            } for t in transactions]

            return Response({
                'kpi': {
                    'income': income,
                    'expenses': expenses,
                    'balance': balance
                },
                'transactions': formatted_transactions
            })
        except requests.exceptions.RequestException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Obtiene los detalles completos de una transacción específica",
        responses={
            200: openapi.Response(
                description="Detalles completos de la transacción",
                examples={
                    "application/json": {
                        "id": "string",
                        "internal_identification": "string",
                        "account": {
                            "id": "string",
                            "link": "string",
                            "institution": {
                                "name": "string",
                                "type": "string"
                            },
                            "name": "string",
                            "category": "string",
                            "balance": {
                                "current": "number",
                                "available": "number",
                                "blocked": "number"
                            }
                        },
                        "amount": "number",
                        "local_currency_amount": "number",
                        "currency": "string",
                        "description": "string",
                        "category": "string",
                        "subcategory": "string",
                        "type": "string",
                        "status": "string",
                        "merchant": {
                            "logo": "string",
                            "website": "string",
                            "merchant_name": "string"
                        },
                        "credit_card_data": {
                            "bill_name": "string",
                            "bill_amount": "number",
                            "card_number": "string"
                        }
                    }
                }
            ),
            404: "Transacción no encontrada"
        }
    )
    @action(detail=True, methods=['get'], url_path='details')
    def transaction_details(self, request, pk=None):
        """
        Obtiene los detalles completos de una transacción específica.
        """
        try:
            response = requests.get(
                f'{settings.BELVO_API_URL}transactions/{pk}/',
                headers=self.get_headers()
            )
            response.raise_for_status()
            transaction = response.json()

            detailed_transaction = {
                'id': transaction['id'],
                'internal_identification': transaction['internal_identification'],
                'account': {
                    'id': transaction['account']['id'],
                    'link': transaction['account']['link'],
                    'institution': transaction['account']['institution'],
                    'name': transaction['account']['name'],
                    'category': transaction['account']['category'],
                    'balance': transaction['account']['balance'],
                    'currency': transaction['account']['currency']
                },
                'amount': transaction['amount'],
                'local_currency_amount': transaction['local_currency_amount'],
                'currency': transaction['currency'],
                'description': transaction['description'],
                'category': transaction['category'],
                'subcategory': transaction.get('subcategory'),
                'type': transaction['type'],
                'status': transaction['status'],
                'merchant': transaction.get('merchant', {}),
                'credit_card_data': transaction.get('credit_card_data', {}),
                'transacted_at': transaction['transacted_at'],
                'created_at': transaction['created_at'],
                'value_date': transaction.get('value_date'),
                'payment_type': transaction.get('payment_type'),
                'operation_type': transaction.get('operation_type'),
                'operation_type_additional_info': transaction.get('operation_type_additional_info'),
                'counterparty': transaction.get('counterparty', {}),
                'loan_data': transaction.get('loan_data', {})
            }

            return Response(detailed_transaction)

        except requests.exceptions.RequestException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_description="Crea y registra links y cuentas de prueba"
    )
    @action(detail=False, methods=['post'])
    def create_test_links(self, request):
        """
        Crea y registra links y cuentas de prueba
        """
        try:
            created_links = []

            for institution_data in TEST_CREDENTIALS:
                try:
                    # 1. Crear el link
                    link_data = {
                        'institution': institution_data['institution'],
                        'username': institution_data['username'],
                        'password': institution_data['password'],
                        'access_mode': 'single'
                    }

                    link_response = requests.post(
                        f'{settings.BELVO_API_URL}links/',
                        headers=self.get_headers(),
                        json=link_data
                    )
                    link_response.raise_for_status()
                    link = link_response.json()
                    
                    # 2. Registrar cuentas para el link
                    register_response = requests.post(
                        f'{settings.BELVO_API_URL}accounts/',
                        headers=self.get_headers(),
                        json={
                            'link': link['id'],
                            'save_data': True
                        }
                    )
                    register_response.raise_for_status()
                    
                    created_links.append({
                        'link': link,
                        'accounts_registered': True
                    })

                except requests.exceptions.RequestException as e:
                    print(f"Error processing {institution_data['institution']}: {str(e)}")
                    if hasattr(e.response, 'text'):
                        print(f"Response: {e.response.text}")
                    continue

            return Response({
                'message': f'Se crearon y registraron {len(created_links)} links exitosamente',
                'links': created_links
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def all_accounts(self, request):
        """
        Obtiene todas las cuentas de todos los links válidos
        """
        try:
            # 1. Obtener todos los links
            links_response = requests.get(
                f'{settings.BELVO_API_URL}links/',
                headers=self.get_headers()
            )
            links_response.raise_for_status()
            links = links_response.json()['results']
            
            print(f"Found {len(links)} links")  # Debug

            # 2. Obtener cuentas para cada link
            institutions_accounts = []
            total_accounts = 0

            for link in links:
                if link['status'] == 'valid':
                    try:
                        # Intentar registrar cuentas primero
                        register_response = requests.post(
                            f'{settings.BELVO_API_URL}accounts/',
                            headers=self.get_headers(),
                            json={
                                'link': link['id'],
                                'save_data': True
                            }
                        )
                        
                        # Obtener cuentas
                        accounts_response = requests.get(
                            f'{settings.BELVO_API_URL}accounts/',
                            headers=self.get_headers(),
                            params={'link': link['id']}
                        )
                        accounts_response.raise_for_status()
                        accounts = accounts_response.json()['results']
                        
                        print(f"Link {link['id']} has {len(accounts)} accounts")  # Debug
                        
                        if accounts:
                            total_accounts += len(accounts)
                            institutions_accounts.append({
                                'institution_name': link['institution'],
                                'link_id': link['id'],
                                'accounts': [{
                                    'id': acc['id'],
                                    'name': acc['name'],
                                    'category': acc['category'],
                                    'balance': acc['balance'],
                                    'currency': acc['currency']
                                } for acc in accounts]
                            })
                    except requests.exceptions.RequestException as e:
                        print(f"Error getting accounts for link {link['id']}: {str(e)}")
                        if hasattr(e.response, 'text'):
                            print(f"Response: {e.response.text}")
                        continue

            return Response({
                'total_accounts': total_accounts,
                'institutions': institutions_accounts
            })

        except requests.exceptions.RequestException as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
