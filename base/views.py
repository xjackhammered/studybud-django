from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.db.models import Q
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserUpdateForm, MyUserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Create your views here.
def loginPage(request):
    page = "login"

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist.')
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request,'Username or password does not exist.')


    return render(request, "base/login_register.html", {"page": page})


def logoutUser(request):
    logout(request)
    return redirect("home")


def registerUser(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "An error has occured during registration.")

    return render(request, "base/login_register.html", {"form":form})



def home(request):
    if request.GET.get('q') != None:
        q = request.GET.get('q')
    else:
        q = ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q)|
        Q(name__contains=q) |
        Q(description__contains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__name__icontains=q))
    
    context = {"rooms": rooms, "topics": topics, "room_count":room_count, "room_messages": room_messages}
    return render(request, "base/home.html", context)


def room(request,pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created') ## getting the messages of a specific room
    participants = room.participants.all()
    
    if request.method == "POST":
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)  ##adding participants in the room
        return redirect("room", pk=room.id)
    
    return render(request, "base/room.html", {"room":room, "room_messages":room_messages, "participants":participants})

def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    return render(request, "base/profile.html", {"user": user, "rooms": rooms, "room_messages":room_messages, "topics":topics})


@login_required(login_url = "login")
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host = request.user,
            topic=topic,
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )
        return redirect("home")

    
    
    return render(request, "base/room_form.html", {'form':form, "topics":topics})


@login_required(login_url = "login")
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse("You're not allowerd here!!")

    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect("home")


    return render(request, "base/room_form.html", {"form":form, "topics":topics, "room":room})


@login_required(login_url = "login")
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    
    if request.user != room.host:
        return HttpResponse("You're not allowed here!!")
    
    if request.method == "POST":
        room.delete()
        return redirect("home")
    return render(request, 'base/delete.html', {'obj':room}) 


@login_required(login_url = "login")
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    
    if request.user != message.user:
        return HttpResponse("You're not allowed here!!")
    
    if request.method == "POST":
        message.delete()
        return redirect("home")
    return render(request, 'base/delete.html', {'obj':message}) 


@login_required(login_url="login")
def updateUser(request):
    form = UserUpdateForm(instance=request.user)

    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=request.user.id)
    return render(request, "base/update-user.html", {"form":form})


def topicsPage(request):
    if request.GET.get('q') != None:
        q = request.GET.get('q')
    else:
        q = ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {"topics":topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {"room_messages":room_messages})