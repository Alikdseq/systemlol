# -*- coding: utf-8 -*-
"""DRF throttles for auth, lookup and broadcast."""

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle, UserRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth"


class LookupRateThrottle(UserRateThrottle):
    scope = "lookup"


class BroadcastRateThrottle(UserRateThrottle):
    scope = "broadcast"
