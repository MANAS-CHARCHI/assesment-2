from rest_framework.serializers import ModelSerializer, Serializer
from .models import User
from rest_framework import serializers
from django.contrib.auth import authenticate 

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'role' ,'first_name', 'last_name', 'DOB', 'phone_number','age', 'date_joined', 'last_login', 'is_active']
        read_only_fields = ['date_joined', 'last_login', 'email', 'is_active', 'age']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'DOB': {'required': False},
            'phone_number': {'required': False},
        }

class LoginSerializer(Serializer):
    email=serializers.EmailField(required=True)
    password=serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials !")
    