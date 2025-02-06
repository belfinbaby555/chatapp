from django.shortcuts import render
from django.http import JsonResponse
import json
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .models import Message

from django.db.models import Q
from django.core.files.storage import FileSystemStorage

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                return JsonResponse({"error": "Username and password required"}, status=200)

            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already taken"}, status=200)

            user = User.objects.create_user(username=username, password=password)
            return JsonResponse({"message": "User registered successfully", "user": username}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=200)

    return JsonResponse({"error": "Only POST allowed"}, status=405)

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return JsonResponse({"error": "Username and password required"}, status=200)

            user = authenticate(username=username, password=password)
            print(f"User found: {user}")  # Debugging line

            if user is not None:
                login(request, user)
                return JsonResponse({"message": "Login successful", "user": username})
            else:
                return JsonResponse({"error": "Invalid credentials"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=200)

    return JsonResponse({"error": "Only POST allowed"}, status=400)

@csrf_exempt
@login_required
def get_user_details(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized. Please log in."}, status=401)

    if request.method == "GET":
        logged_in_user = request.user.username
        other_users = User.objects.exclude(username=logged_in_user).values_list("username", flat=True)

        return JsonResponse({
            "logged_in_user": logged_in_user,
            "other_users": list(other_users),
            "bool":True,
        }, status=200)

    return JsonResponse({"error": "Only GET allowed"}, status=405)

@csrf_exempt
@login_required
def get_messages(request):
    if request.method == "GET":
        recipient_username = request.GET.get("recipient")

        if not recipient_username:
            return JsonResponse({"error": "Recipient username required"}, status=400)

        try:
            recipient = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
            return JsonResponse({"error": "Recipient does not exist"}, status=404)

        messages = Message.objects.filter(
            (Q(sender=request.user, recipient=recipient) |
             Q(sender=recipient, recipient=request.user))
        ).order_by("timestamp")

        messages_data = [
            {
                "sender": message.sender.username,
                "recipient": message.recipient.username,
                "content": message.content,
                "image": message.image.url if message.image else None,
                "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for message in messages
        ]

        return JsonResponse({"messages": messages_data}, status=200)

    return JsonResponse({"error": "Only GET allowed"}, status=405)

@csrf_exempt
@login_required
def send_message(request):
    if request.method == "POST":
        recipient_username = request.POST.get("recipient")
        content = request.POST.get("content", "").strip()
        image = request.FILES.get("image")

        if not recipient_username:
            return JsonResponse({"error": "Recipient username is required"}, status=400)

        try:
            recipient = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
            return JsonResponse({"error": "Recipient does not exist"}, status=404)

        if not content and not image:
            return JsonResponse({"error": "Message content or image required"}, status=400)

        image_url = None
        if image:
            file_name = default_storage.save(f"chat_images/{image.name}", image)
            image_url = request.build_absolute_uri(settings.MEDIA_URL + file_name)

        message = Message.objects.create(
            sender=request.user, recipient=recipient, content=content, image=image
        )

        return JsonResponse({
            "sender": request.user.username,
            "recipient": recipient.username,
            "content": message.content,
            "image": image_url if image else None,
            "timestamp": message.timestamp,
        }, status=201)

    return JsonResponse({"error": "Only POST allowed"}, status=400)
