import structlog
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()

# One logger per module, named after it ("apps.users.views"); django-structlog
# binds request_id / user_id onto every line for free.
log = structlog.get_logger(__name__)


class AuthThrottleMixin:
    """Applies the strict ``auth`` rate scope and logs throttle hits.

    Mixed into the public auth endpoints (login/register) to blunt
    brute-force. Single responsibility: the throttle policy and its
    observability, kept out of each view's own logic (DRY across the two).
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def throttled(self, request, wait):
        log.warning(
            "auth_throttled",
            scope=self.throttle_scope,
            email=request.data.get("email"),
            wait_seconds=round(wait) if wait else None,
        )
        super().throttled(request, wait)


class RegisterView(AuthThrottleMixin, generics.CreateAPIView):
    """POST /auth/register/ — open registration."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Business event: machine name + structured fields, never the password.
        log.info("user_registered", user_id=user.id, email=user.email)


class LoginView(AuthThrottleMixin, TokenObtainPairView):
    """POST /auth/login/ — SimpleJWT token issuance, plus auth-event logging.

    A thin subclass that wraps the inherited ``post`` (Template Method hook):
    SimpleJWT still does all the token work; we only add an observability
    layer around its outcome. We log the email and the reason, never the
    password.
    """

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed as exc:
            log.warning("login_failed", email=email, reason=str(exc.detail))
            raise
        log.info("login_succeeded", email=email)
        return response


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /users/me/ — the authenticated user's own profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
