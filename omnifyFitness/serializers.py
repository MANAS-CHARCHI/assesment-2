from rest_framework.serializers import ModelSerializer, Serializer
from .models import *
from rest_framework import serializers
from datetime import datetime, timedelta

class ClassTypeSerializer(ModelSerializer):
    class Meta:
        model = ClassType
        fields = '__all__'
class RecurringSessionsSerializer(serializers.ModelSerializer):
    class_type = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ClassType.objects.all()
    )
    day_of_week = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )
    duration_minutes = serializers.IntegerField(write_only=True)
    start_time = serializers.TimeField()
    day_of_week_display = serializers.SerializerMethodField(read_only=True)
    time_utc = serializers.SerializerMethodField(read_only=True)
    instructor_email = serializers.EmailField(write_only=True)

    class Meta:
        model = Sessions
        fields = [
            'class_type',
            'day_of_week',
            'day_of_week_display',
            'start_time',
            'duration_minutes',
            'time_utc',
            'capacity',
            'instructor_email',
            'instructor',
            'end_time',
        ]
        read_only_fields = ['instructor', 'end_time']

    def get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()

    def validate_day_of_week(self, values):
        day_map = {
            'sunday': 0, 'sun': 0,
            'monday': 1, 'mon': 1,
            'tuesday': 2, 'tue': 2,
            'wednesday': 3, 'wed': 3,
            'thursday': 4, 'thu': 4,
            'friday': 5, 'fri': 5,
            'saturday': 6, 'sat': 6,
        }
        result = []
        for value in values:
            key = value.lower().strip()
            if key not in day_map:
                raise serializers.ValidationError(f"Invalid day: {value}")
            result.append(day_map[key])
        return result

    def validate_instructor_email(self, email):
        try:
            instructor = User.objects.get(email=email)
            if instructor.role != 'INSTRUCTOR':
                raise serializers.ValidationError("User is not an instructor.")
        except User.DoesNotExist:
            raise serializers.ValidationError("Instructor with this email does not exist.")
        return email

    def get_time_utc(self, obj):
        return obj.start_time.strftime('%H:%M:%S') + ' UTC'

    def validate(self, attrs):
        return attrs
    
    DAY_NAME_MAP = {
        0: "Sunday",
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
    }
    def create(self, validated_data):
        day_of_weeks = validated_data.pop('day_of_week')
        duration = validated_data.pop('duration_minutes')
        instructor_email = validated_data.pop('instructor_email')

        try:
            instructor = User.objects.get(email=instructor_email)
            if instructor.role != 'INSTRUCTOR':
                raise serializers.ValidationError("User is not an instructor.")
        except User.DoesNotExist:
            raise serializers.ValidationError("Instructor with this email does not exist.")

        validated_data['instructor'] = instructor
        start_time = validated_data['start_time']
        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = start_dt + timedelta(minutes=duration)
        validated_data['end_time'] = end_dt.time()

        conflict_errors = []
        for day in day_of_weeks:
            if Sessions.objects.filter(
                class_type=validated_data['class_type'],
                day_of_week=day,
                start_time=start_time
            ).exists():
                raise serializers.ValidationError({
                    f"A session with class '{validated_data['class_type'].name}' already exists on {self.DAY_NAME_MAP.get(day)} at {start_time.strftime('%H:%M')}."
                })
            overlapping_sessions = Sessions.objects.filter(
                instructor=instructor,
                day_of_week=day
            ).filter(
                start_time__lt=validated_data['end_time'],
                end_time__gt=start_time
            )
            if overlapping_sessions.exists():
                time_ranges = [
                    f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
                    for s in overlapping_sessions
                ]
                times_str = "; ".join(time_ranges)
                conflict_errors.append(
                    f"Instructor '{instructor.email}' is already scheduled on {self.DAY_NAME_MAP.get(day)} during: {times_str}."
                )
        
            
            created_instances = []
            sessions_data = validated_data.copy()
            sessions_data['day_of_week'] = day
            instance = Sessions.objects.create(**sessions_data)
            created_instances.append(instance)
        if conflict_errors:
            raise serializers.ValidationError(conflict_errors)
        return created_instances[0]
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        if user.role != 'ADMIN':
            raise serializers.ValidationError("Only admin users can update schedules.")

        duration = validated_data.pop('duration_minutes', None)
        instructor_email = validated_data.pop('instructor_email', None)
        day_of_weeks = validated_data.pop('day_of_week', [instance.day_of_week])

        if instructor_email:
            try:
                instructor = User.objects.get(email=instructor_email)
                if instructor.role != 'INSTRUCTOR':
                    raise serializers.ValidationError("User is not an instructor.")
            except User.DoesNotExist:
                raise serializers.ValidationError("Instructor with this email does not exist.")
        else:
            instructor = instance.instructor

        validated_data['instructor'] = instructor

        # Update start_time or keep old
        start_time = validated_data.get('start_time', instance.start_time)

        # Duration fallback
        if duration is not None:
            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.time()
        else:
            end_time = instance.end_time

        validated_data['end_time'] = end_time

        # Perform conflict check
        conflict_errors = []
        for day in day_of_weeks:
            overlapping_sessions = Sessions.objects.filter(
                instructor=instructor,
                day_of_week=day
            ).exclude(pk=instance.pk).filter(
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if overlapping_sessions.exists():
                time_ranges = [
                    f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
                    for s in overlapping_sessions
                ]
                times_str = "; ".join(time_ranges)
                conflict_errors.append(
                    f"Instructor '{instructor.email}' is already scheduled on {self.DAY_NAME_MAP.get(day)} during: {times_str}."
                )

        if conflict_errors:
            raise serializers.ValidationError({"errors": conflict_errors})

        # Apply updates
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.day_of_week = day_of_weeks[0]  # Use only the first day for update
        instance.save()

        return instance
    

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['class_session']
    
    def validate(self, attrs):
        session = attrs['class_session']
        current_bookings = Booking.objects.filter(class_session=session).count()

        if current_bookings >= session.capacity:
            raise serializers.ValidationError(f"Session is full. Max capacity of {session.capacity} reached.")

        return attrs