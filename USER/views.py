from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction


from .models import (
    PasswordReset, 
    ActivateAccount,
    PasswordReset,
    UserRole
    )
from .serializers import (
    UserSerializer, 
    LoginSerializer
    )
User=get_user_model()

class RegisterView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role", UserRole.CLIENT)
        
        # Ensure only valid roles are accepted
        if role not in UserRole.values:
            return Response(
                {"error": f"Invalid role '{role}'. Must be one of: {', '.join(UserRole.values)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not email or not password:
            return Response(
                {"error": "Both email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            with transaction.atomic():

                user = User.objects.create_user(email=email, password=password, role=role)
                ActivateAccount.objects.create(email=user)
                print(f'curl -X POST http://127.0.0.1:8000/user/activate/{ActivateAccount.objects.get(email=user).token}')
                response = Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
 
        except Exception as e:
            response = Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return response

class LoginView(APIView):
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                user=serializer.validated_data
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                response=Response(
                    {"user": {
                        "email": user.email, 
                        "first_name":user.first_name, 
                        "last_name": user.last_name,
                        "last_login": user.last_login,
                        "date_joined": user.date_joined,
                        "is_active": user.is_active
                        }
                    },status=status.HTTP_200_OK) 
                response.set_cookie(key="access_token",
                                value=access_token, 
                                httponly=True,
                                samesite="None",
                                secure=True,
                                max_age= 30 * 60,
                                path="/",
                                )
                response.set_cookie(key="refresh_token",
                                value=str(refresh),
                                httponly=True,
                                samesite="None",
                                secure=True,
                                max_age= 7 * 24 * 60 * 60,
                                path="/",
                                )
                return response
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:  
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    # permission_class=[IsAuthenticated]
    def post(self, request):
        refresh_token=request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                refresh.blacklist()
            except Exception as e:
                return Response({"error": "Error Invalidate token"}, status=status.HTTP_401_UNAUTHORIZED)
            response=Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        else:
            response=Response({"message": "You are not logged in"}, status=status.HTTP_200_OK)
        try:
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
        except:
            pass
        return response

class UpdateUserView(APIView):
    permission_classes=[IsAuthenticated]
    def put(self, request):
        user=request.user
        if user.email != request.data.get("email"):
            return Response({"error": "Email cannot be changed"}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get("password"):
            return Response({"error": "Password cannot be changed"}, status=status.HTTP_400_BAD_REQUEST)
        serializer=UserSerializer(user, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            try:        
                user=serializer.save()
                return Response({"message": "User updated successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        try:
            user = request.user
            serializer=UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Unknown error in User profile view"}, status=status.HTTP_401_UNAUTHORIZED)

  
class CookieTokenRefreshView(APIView):
    def post(self, request):
        refresh_token=request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token not found in cookies"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            response=Response({"message": "Token refreshed successfully"}, status=status.HTTP_200_OK)
            response.set_cookie(key="access_token",
                                value=access_token, 
                                httponly=True,
                                samesite="None",
                                secure=True,
                                max_age= 30 * 60,
                                path="/",
                                )
            return response
        except InvalidToken:
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
        
class VerifyUserView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request):
        return Response({"message": "User authenticated successfully"}, status=status.HTTP_200_OK)

class ForgetPasswordView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not exist"}, status=status.HTTP_404_NOT_FOUND)
        try:
            forget_password = PasswordReset.objects.create(email=user)
            print()

            return Response({"message": "Password reset link sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class changeForgetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, email, token):
        print(email, token)
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not email or not token:
            return Response({"error": "Email and token are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            email=User.objects.get(email=email)
            forget_password = PasswordReset.objects.filter(email=email, token=token).first()
            if not forget_password:
                return Response({"error": "Invalid token or expired."}, status=status.HTTP_400_BAD_REQUEST)

            if password != confirm_password:
                return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            user.set_password(password)
            user.save()
            forget_password.delete()

            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


        
        
class ChangePasswordView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        recent_password = request.data.get("password")
        password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        if recent_password != request.user.password:
            return Response({"error": "Incorrect current password"}, status=status.HTTP_400_BAD_REQUEST)
        if password != confirm_password:
            return Response({"error": "New Password does not match"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=request.email).first()
        if not user:
            return Response({"error": "User not exist"}, status=status.HTTP_404_NOT_FOUND)
        try:
            user.set_password(password)
            user.save()
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
class ActivateAccountView(APIView):
    def post(self, request, *args, **kwargs):
        token = kwargs.get("token")
        try:
            activate_account = ActivateAccount.objects.get(token=token)
            if not activate_account:
                return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(email=activate_account.email)
            if not user:
                return Response({"error": "User not exist"}, status=status.HTTP_404_NOT_FOUND)
            with transaction.atomic():
                user.is_active = True
                user.save()
                activate_account.delete()
                return Response({"message": f"{user.email} Account activated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)