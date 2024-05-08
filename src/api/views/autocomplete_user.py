from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model
from django.db.models import Q


@extend_schema(
    tags=['autocomplete'],
    parameters=[
        OpenApiParameter(
            name='q',
            description='Query string for searching user names',
            required=True,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='type',
            description='Type of the search, only supports "users"',
            required=True,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='limit',
            description='Maximum number of users to return',
            required=True,
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses={
        200: OpenApiResponse(description=''),
        400: OpenApiResponse(description='Invalid parameters'),
        403: OpenApiResponse(description='Access not allowed'),
    },
)
class AutocompleteUserView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Definition:
            https://base-angewandte-docs.readthedocs.io/en/latest/api_principles.html#autocomplete-endpoint

        This implementation allows to get autocomplete suggestions by
        users' names (specifically by first name, last name or username)
        """
        # TODO: copy definition instead of referencing it, the link or its content could change

        # ------ base cases, validations ------
        try:
            query = request.query_params['q']
            query_type = request.query_params['type']
            limit = request.query_params['limit']
        except KeyError as e:
            return Response(
                f'Missing required parameter: {e}', status=status.HTTP_400_BAD_REQUEST
            )

        try:
            limit = int(limit)
            if limit <= 0:
                raise ValueError
        except ValueError:
            return Response(
                'Invalid "limit" parameter, must be a positive integer',
                status=status.HTTP_400_BAD_REQUEST,
            )
        if query_type != 'users':
            return Response(
                'Invalid "type" parameter. Supported types: users',
                status=status.HTTP_400_BAD_REQUEST,
            )

        # avoids matching everything when using __icontains
        if query == '':
            return Response(
                'Invalid "q" parameter. It cannot be empty',
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------

        matched_users = get_user_model().objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query),
            is_active=True,
        )[:limit]

        response_data = [
            {'id': user.username, 'label': user.get_full_name()}
            for user in matched_users
        ]

        return Response(response_data)


"""
Code challenge comments
    I did not generalise it for different possible query types because of the YAGNI principle

Out of scope for this challenge, in a real-world scenario I would:
    1. consider implementing further limit validation (upper limit, for instance)
    2. consider making some query params optional, like limit and type
    3. consider supporting regex with field__iregex

    4. consider adding throttling
    5. consider adding pagination
    6. consider adding caching

    7. add a test suite
"""
