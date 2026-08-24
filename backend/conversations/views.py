from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .ai_gateway import AIGateway

class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        ).prefetch_related("messages")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        # 1. Get conversation belonging to logged-in user
        conversation = get_object_or_404(
            Conversation,
            id=self.kwargs["conversation_id"],
            user=request.user
        )

        # 2. Validate incoming message
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 3. Save user message
        user_message = serializer.save(
            conversation=conversation,
            role="user"
        )

        if conversation.title == "New Chat":
            title = user_message.content.strip()

            if len(title) > 35:
                title = title[:35].rstrip() + "..."

            conversation.title = title
            conversation.save(update_fields=["title", "updated_at"])

        # 4. Get complete conversation history
        previous_messages = conversation.messages.order_by("created_at")

        messages = []

        for message in previous_messages:
            messages.append({
                "role": message.role,
                "content": message.content
            })

        # 5. Send history to Groq
        try:
            ai = AIGateway()

            ai_response = ai.generate_response(messages)

        except Exception as e:
            return Response(
                {
                    "error": "AI service failed",
                    "detail": str(e),
                    "user_message": MessageSerializer(
                        user_message
                    ).data
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        # 6. Save AI response
        if isinstance(ai_response, str):
            ai_content = ai_response
            model_used = None
            provider = "groq"
            fallback_used = False

        else:
            ai_content = ai_response.get("content", "")
            model_used = ai_response.get("model_used")
            provider = ai_response.get("provider", "groq")
            fallback_used = ai_response.get(
                "fallback_used",
                False
            )


        assistant_message = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=ai_content,
            model_used=model_used,
            provider=provider,
            fallback_used=fallback_used
        )

        # 7. Update conversation timestamp
        conversation.save()

        # 8. Return both messages
        return Response(
            {
                "user_message": MessageSerializer(
                    user_message
                ).data,
                "assistant_message": MessageSerializer(
                    assistant_message
                ).data
            },
            status=status.HTTP_201_CREATED
        )

class ConversationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            user=self.request.user
        ).prefetch_related("messages")