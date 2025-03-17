from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
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
    EasyPayCallbackView,
    InitiatePaymentView,
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
    view_available_buses,
    RegisterView,
    CsrfTestView,
    ChangePasswordView,
    manage_buses,
    booking_stats,
    EditProfileView,
    profile_json_view,
    confirm_booking,
    PaymentProcessView,
    
    )


schema_view = get_schema_view(
    openapi.Info(
        title="BusKing API",
        default_version='v1',
        description="API documentation for BusKing Project",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [

    path('csrf-test/', CsrfTestView.as_view(), name='csrf-test'),

    path('admin/manage-buses/', manage_buses, name='manage-buses'),
    path('admin/booking-stats/', booking_stats, name='booking-stats'),
    
    path('csrf-token/', CSRFTokenView.as_view(), name='csrf_token'),
    path('token/obtain/', CustomTokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token-refresh'),

    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('edit-profile/', EditProfileView.as_view(), name='edit-profile'),
    path('user/profile/', profile_json_view, name='profile-json-view'),

    path('change_password/', ChangePasswordView.as_view(), name='change-password'),
    path('login/', UserAuthView.as_view(), name='user-auth'),
    path('register/', RegisterView.as_view(), name='register'), 
    path('logout/', UserLogoutView.as_view(), name='user-logout'),

    path('merchants/', MerchantListView.as_view(), name='merchant-list'),
    path('merchants/<int:pk>/', MerchantDetailView.as_view(), name='merchant-detail'),
    path('merchants/<int:merchant_id>/approve/', ApproveMerchantView.as_view(), name='approve-merchant'),

    path('buses/<int:bus_id>/book/<int:number_of_seats>/', BookingListCreateView.as_view(), name='book-bus'),
    path('buses/<int:pk>/', BusRetrieveUpdateDestroyView.as_view(), name='bus-detail'), 
    path('buses/', BusListView.as_view(), name='bus-list'), 
    path('buses/create/', BusCreateView.as_view(), name='bus-create'),
    path('available_buses/', view_available_buses, name='available_buses'),

    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<int:pk>/', BookingRetrieveUpdateDestroyView.as_view(), name='booking-detail'),
    path('bookings/confirm/<int:booking_id>/', confirm_booking, name='confirm_booking'),
    
    path('payment-callback/', EasyPayCallbackView.as_view(), name='payment-callback'),
    path('initiate-payment/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('payment/process/<int:booking_id>/', PaymentProcessView.as_view(), name='payment-process'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'),

    path('routes/', views.RouteListView.as_view(), name='route-list'),
    path('routes/<int:pk>/', views.RouteDetailView.as_view(), name='route-detail'),
    path('routes/create/', views.RouteCreateView.as_view(), name='route-create'),

    path('destinations/', DestinationListView.as_view(), name='destination-list'),
    path('destinations/create/', CreateDestinationView.as_view(), name='create-destination'),
    path('destinations/<int:pk>/', DestinationDetailView.as_view(), name='destination-detail'), 

    path('payment-page/', views.payment_page, name='payment_page'),
    path('create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
 
]
