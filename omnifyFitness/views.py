from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from omnifyFitness.models import *
from omnifyFitness.serializers import *
from USER.models import *
from django.shortcuts import get_object_or_404

# Create your views here.

class getClassTypes(APIView):
    def get(self, request):
        classTypes = ClassType.objects.all()
        serializer = ClassTypeSerializer(classTypes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != UserRole.ADMIN:
            return Response(
                {"error": "Only admin users can create schedules."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RecurringSessionsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                return Response({"message": "Session created successfully."}, status=status.HTTP_201_CREATED)
            else:
                return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, **kwargs):
        if request.user.role != UserRole.ADMIN:
            return Response({"error": "Only admin users can update schedules."}, status=status.HTTP_403_FORBIDDEN)

        try:
            session = Sessions.objects.get(pk=kwargs.get('pk'))
        except Sessions.DoesNotExist:
            return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RecurringSessionsSerializer(session, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Schedule updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, **kwargs):
        if request.user.role != UserRole.ADMIN:
            return Response(
                {"error": "Only admin users can delete schedules."},
                status=status.HTTP_403_FORBIDDEN
            )
        schedule = Sessions.objects.get(pk=kwargs.get('pk'))
        schedule.delete()
        return Response({"message": "Schedule deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class SessionListView(APIView):
    def get(self, request):
        sessions = Sessions.objects.all()
        serializer = RecurringSessionsSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class BookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != UserRole.CLIENT:
            return Response({"error": "Only client users can book sessions."}, status=status.HTTP_403_FORBIDDEN)
        user = request.user
        serializer = BookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        if Booking.objects.filter(user=user, class_session=serializer.validated_data['class_session']).exists():
            return Response({"error": "You have already booked this session."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save(user=user)
                return Response({"message": "Booking created successfully."}, status=status.HTTP_201_CREATED)
            else:
                return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as e:
            return Response({'errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, **kwargs):
        if request.user.role != UserRole.CLIENT:
            return Response({"error": "Only client users can delete bookings."}, status=status.HTTP_403_FORBIDDEN)
        booking = get_object_or_404(Booking, pk=kwargs.get('pk'), user=request.user)
        booking.delete()
        return Response({"message": "Booking deleted successfully."}, status=status.HTTP_204_NO_CONTENT )
    
class InstructorBookingView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, **kwargs):
        if request.user.role != UserRole.INSTRUCTOR:
            return Response({"error": "Only instructor can delete bookings for everyone."}, status=status.HTTP_403_FORBIDDEN)
        session= get_object_or_404(Sessions, pk=kwargs.get('pk'))
        session.delete()
        return Response({"message": "Session deleted successfully."}, status=status.HTTP_204_NO_CONTENT )

    def get(self, request):
        if request.user.role != UserRole.INSTRUCTOR:
            return Response({"error": "Only instructor access this view."}, status=status.HTTP_403_FORBIDDEN)
        bookings = Sessions.objects.filter(instructor=request.user)
        serializer = RecurringSessionsSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)