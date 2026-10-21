from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/form.html",
        extra_context={"title": "Reset your password", "button": "Send reset link"},
    ), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/message.html",
        extra_context={"title": "Check your email", "text": "If an account exists for that address, we sent a reset link."},
    ), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/form.html",
        extra_context={"title": "Choose a new password", "button": "Save password"},
    ), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/message.html",
        extra_context={"title": "Password changed", "text": "You can now log in with your new password."},
    ), name="password_reset_complete"),
]