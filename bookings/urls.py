from django.urls import path
from .views import (
    UserListCreateView, 
    book_bus, 
    UserRetrieveUpdateDestroyView, 
    BusListCreateView, 
    BusRetrieveUpdateDestroyView, 
    BookingListCreateView, 
    BookingRetrieveUpdateDestroyView, 
    MerchantListView, 
    MerchantDetailView, 
    CustomerListView, 
    CustomerDetailView,
    ApproveMerchantView  # Added ApproveMerchantView import
)

urlpatterns = [
    # User URLs
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),

    # Merchant URLs
    path('merchants/', MerchantListView.as_view(), name='merchant-list'),
    path('merchants/<int:pk>/', MerchantDetailView.as_view(), name='merchant-detail'),
    path('merchants/approve/', ApproveMerchantView.as_view(), name='approve-merchant'),  # Added URL for approving merchants

    # Bus URLs
    path('buses/', BusListCreateView.as_view(), name='bus-list-create'),
    path('buses/<int:pk>/', BusRetrieveUpdateDestroyView.as_view(), name='bus-detail'),
    path('buses/<int:bus_id>/book/<int:number_of_seats>/', book_bus, name='book-bus'),  # To book seats on a bus

    # Booking URLs
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<int:pk>/', BookingRetrieveUpdateDestroyView.as_view(), name='booking-detail'),

    # Customer URLs
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'),
]
