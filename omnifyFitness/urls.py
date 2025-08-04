from django.urls import path
from omnifyFitness.views import *

urlpatterns = [
    path('classTypes', getClassTypes.as_view()),
    path('admin/session/create', SessionView.as_view()),
    path('admin/session/update/<pk>', SessionView.as_view()),
    path('admin/session/delete/<pk>', SessionView.as_view()),
    path('admin/session', SessionListView.as_view()),
    path('client/booking', BookingView.as_view()),
    path('client/booking/<pk>', BookingView.as_view()),
    path('instructor/booking/delete/<pk>', InstructorBookingView.as_view()),
    path('instructor/booking', InstructorBookingView.as_view()),
]

