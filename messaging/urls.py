"""
URL configuration for the 'messaging' app.

Uses a nested router to link Messages to Conversations.
"""

from rest_framework_nested import routers
from .views import ConversationViewSet, MessageViewSet

# Main router
router = routers.DefaultRouter()
# /api/v1/conversations/
router.register(r"conversations", ConversationViewSet, basename="conversation")

# Nested router for /api/v1/conversations/<conversation_pk>/messages/
conversations_router = routers.NestedSimpleRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', MessageViewSet, basename='conversation-messages')

# Combine the URL patterns
urlpatterns = router.urls + conversations_router.urls