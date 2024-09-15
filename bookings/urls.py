from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    UserListCreateView,
    UserRetrieveUpdateDestroyView,
    BusListCreateView,
    BusRetrieveUpdateDestroyView,
    BookingListCreateView,
    BookingRetrieveUpdateDestroyView,
    MerchantListView,
    MerchantDetailView,
    CustomerListView,
    CustomerDetailView,
    ApproveMerchantView,
    BookBusView,
    SearchBusesView,
    EasyPayCallbackView,
    InitiatePaymentView,
    browse_buses,
)

urlpatterns = [
    # User URLs
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', auth_views.PasswordChangeView.as_view(), name='password_change'),

    # Merchant URLs
    path('merchants/', MerchantListView.as_view(), name='merchant-list'),
    path('merchants/<int:pk>/', MerchantDetailView.as_view(), name='merchant-detail'),
    path('merchants/approve/', ApproveMerchantView.as_view(), name='approve-merchant'),

    # Bus URLs
    path('buses/', BusListCreateView.as_view(), name='bus-list-create'),
    path('buses/<int:pk>/', BusRetrieveUpdateDestroyView.as_view(), name='bus-detail'),
    path('buses/<int:bus_id>/book/<int:number_of_seats>/', BookBusView.as_view(), name='book-bus'),
    path('search-buses/', SearchBusesView.as_view(), name='search_buses'),
    path('browse-buses/', browse_buses, name='browse_buses'),


    # Booking URLs
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<int:pk>/', BookingRetrieveUpdateDestroyView.as_view(), name='booking-detail'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),

    # Payment URLs
    #path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('payment-callback/', EasyPayCallbackView.as_view(), name='payment-callback'),
    path('initiate-payment/', InitiatePaymentView.as_view(), name='initiate_payment'),

    # Customer URLs
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'),

    # Guest routes
    path('buses/', views.browse_buses, name='browse_buses'),
    path('buses/<int:bus_id>/', views.bus_details, name='bus_details'),

    # Registered user routes
    path('book-ticket/', views.book_ticket, name='book_ticket'),
    path('booking-history/', views.booking_history, name='booking_history'),

    # Admin routes
    #path('admin/', admin.site.urls),
    path('admin/manage-buses/', views.manage_buses, name='manage_buses'),
    path('admin/booking-stats/', views.booking_stats, name='booking_stats'),
]
