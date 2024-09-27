from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    UserListCreateView,
    UserRetrieveUpdateDestroyView,
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
    CreateDestinationView,
    DestinationDetailView,
    BusListView, 
    BusCreateView,
    UserAuthView,
    CSRFTokenView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    UserAuthView, 
    UserLogoutView,
    DestinationListView,

)

urlpatterns = [

    path('csrf-token/', CSRFTokenView.as_view(), name='csrf_token'),
    path('token/obtain/', CustomTokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),

    # User URLs
     # User management
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),

    # User Registration
    path('register/', views.register, name='register'),

        # Authentication
    path('login/', UserAuthView.as_view(), name='user-auth'), 
    path('logout/', UserLogoutView.as_view(), name='user-logout'),

    # Profile / Password Change
    path('profile/', auth_views.PasswordChangeView.as_view(), name='password_change'),

    # Merchant URLs
    path('merchants/', MerchantListView.as_view(), name='merchant-list'),
    path('merchants/<int:pk>/', MerchantDetailView.as_view(), name='merchant-detail'),
    path('merchants/approve/', ApproveMerchantView.as_view(), name='approve-merchant'),

    #bus URLS
    path('buses/<int:pk>/', BusRetrieveUpdateDestroyView.as_view(), name='bus-detail'), 
    path('buses/<int:bus_id>/book/<int:number_of_seats>/', BookBusView.as_view(), name='book-bus'),
    path('search-buses/', SearchBusesView.as_view(), name='search_buses'),
    path('buses/', BusListView.as_view(), name='bus-list'), 
    path('buses/create/', BusCreateView.as_view(), name='bus-create'),
    
    # Booking URLs
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<int:pk>/', BookingRetrieveUpdateDestroyView.as_view(), name='booking-detail'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),

    # Payment URLs
    path('payment-callback/', EasyPayCallbackView.as_view(), name='payment-callback'),
    path('initiate-payment/', InitiatePaymentView.as_view(), name='initiate_payment'),

    # Customer URLs
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'),

    # Registered user routes
    path('book-ticket/', views.book_ticket, name='book_ticket'),
    path('booking-history/', views.booking_history, name='booking_history'),

    # Admin routes
    path('admin/manage-buses/', views.manage_buses, name='manage_buses'),
    path('admin/booking-stats/', views.booking_stats, name='booking_stats'),

    # Route Endpoints
    path('routes/', views.RouteListView.as_view(), name='route-list'),
    path('routes/<int:pk>/', views.RouteDetailView.as_view(), name='route-detail'),
    path('routes/create/', views.RouteCreateView.as_view(), name='route-create'),

    #Distination and Route
    path('destinations/', DestinationListView.as_view(), name='destination-list'),
    path('destinations/create/', CreateDestinationView.as_view(), name='create-destination'),
    path('destinations/<int:pk>/', DestinationDetailView.as_view(), name='destination-detail'),  # For details
]
