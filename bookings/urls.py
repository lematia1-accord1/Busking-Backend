from django.urls import path
from .views import UserListCreateView, UserRetrieveUpdateDestroyView, BusListCreateView, BusRetrieveUpdateDestroyView, BookingListCreateView, BookingRetrieveUpdateDestroyView

urlpatterns = [
    # User URLs
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),

    # Bus URLs
    path('buses/', BusListCreateView.as_view(), name='bus-list-create'),
    path('buses/<int:pk>/', BusRetrieveUpdateDestroyView.as_view(), name='bus-detail'),

    # Booking URLs
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<int:pk>/', BookingRetrieveUpdateDestroyView.as_view(), name='booking-detail'),
]
