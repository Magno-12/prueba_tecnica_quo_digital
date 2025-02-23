from rest_framework import serializers


class AuthenticationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
