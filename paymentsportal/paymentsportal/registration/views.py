from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import qrcode
from io import BytesIO
import base64
from .models import Document, Transaction, UserProfile
from django.views.decorators.csrf import csrf_exempt
import json
from .voice_commands import listen_command, speak
import speech_recognition as sr
from .forms import ChangeImageForm, ImageUploadForm
from django.utils.translation import gettext as _

@login_required(login_url='login')
def HomePage(request):
    return render(request, 'home.html', {'username': request.user.username})

@login_required(login_url='login')
def change_image(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ChangeImageForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ChangeImageForm(instance=profile)

    return render(request, 'change_image.html', {'form': form})

def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('pass')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return HttpResponse("Username or Password is incorrect!", status=401)

    return render(request, 'login.html')

def SignupPage(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            return HttpResponse("Your password and confirm password are not the same!", status=400)
        
        if User.objects.filter(username=uname).exists():
            return HttpResponse("Username already exists. Please choose another one.", status=400)

        if User.objects.filter(email=email).exists():
            return HttpResponse("Email is already registered.", status=400)
        
        my_user = User.objects.create_user(uname, email, pass1)
        my_user.save()
        return redirect('login')

    return render(request, 'signup.html')

@login_required(login_url='login')
def LogoutPage(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def pay(request):
    return render(request, 'pay.html', {'username': request.user.username})

@login_required(login_url='login')
def qr_code_view(request):
    qr_image = None
    if request.method == 'POST':
        upi_id = request.POST.get('upi_id')
        amount = request.POST.get('amount', '')

        if upi_id:
            upi_url = f"upi://pay?pa={upi_id}&pn=Your Name&am={amount}&cu=INR"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(upi_url)
            qr.make(fit=True)

            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_image = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'qrcode.html', {'qr_image': qr_image, 'username': request.user.username})

@login_required(login_url='login')
def transactions_page(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'transactions.html', {'transactions': transactions, 'username': request.user.username})

def settings(request):
    return render(request, 'settings.html', {'username': request.user.username})

def ReadingPage(request):
    document = Document.objects.first()
    context = {
        'content': document.content if document else "No content available.",
        'audio_file': document.audio_file.url if document and document.audio_file else None
    }
    return render(request, 'reading.html', context)

@csrf_exempt
def handle_voice_command(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        command = data.get('command')

        if command == 'go to home':
            return redirect('home')
        elif command == 'view transactions':
            return redirect('transactions')
        elif command == 'view settings':
            return redirect('settings')
        elif command == 'read document':
            return redirect('reading')
        else:
            return HttpResponse("Command not recognized", status=400)

    return HttpResponse("Invalid request", status=400)

def voice_control(request):
    if request.method == 'POST':
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)

            try:
                text = recognizer.recognize_google(audio)
                response_data = {"message": "Command received", "text": text}
            except sr.UnknownValueError:
                response_data = {"error": "Could not understand audio"}
            except sr.RequestError as e:
                response_data = {"error": f"Could not request results; {e}"}

        return JsonResponse(response_data)
    
    return render(request, 'voice_control.html')
