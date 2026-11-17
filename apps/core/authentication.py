from rest_framework_simplejwt.authentication import JWTAuthentication


class RelaxedJWTAuthentication(JWTAuthentication):
    """
    Relaxed JWT Authentication:
    - If valid Bearer token provided: authenticates user (request.user = user).
    - If invalid or expired token provided: returns None instead of raising
      AuthenticationFailed. DRF treats the request as unauthenticated (AnonymousUser).
    - For protected endpoints with IsAuthenticated, permission check will still
      fail with 401 Unauthorized as expected.
    - For public endpoints with AllowAny (like devotional artis, catalog, etc.),
      requests succeed gracefully even if the client's browser still holds a stale token.
    """
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception:
            return None
