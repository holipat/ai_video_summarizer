from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from pytube import YouTube
from django.conf import settings
import os
import assemblyai as aai
import openai
from pydub import AudioSegment
# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

def test_view():
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")

@csrf_exempt
def generate_article(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']

        except(KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data send'}, status=400)
        
        #get yt title
        title = yt_title(yt_link)
        print("basligi aldik")
        
        test_view()
        #get transcript
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': 'Failed to get transcript'}, status=500)
        
        #use OpenAI to generate the article
        article_content = generate_article_from_transcription(transcription)
        if not article_content:
            return JsonResponse({'error': 'Failed to generate article'}, status=500)
        
        #save article to database
        
        #return article as response
        return JsonResponse({'content': article_content})
        
    else:
        return JsonResponse({'error':'Invalid request method'}, status=405)

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):
    print("Download starting...")

    try:
        yt = YouTube(link)
        print(f"Video Title: {yt.title}")

        # Fetch available streams for debugging
        streams = yt.streams.filter(only_audio=True)
        print(f"Available audio streams: {streams}")
        
        # Get the first available audio stream
        video = streams.first()

        if not video:
            print("No audio streams available.")
            return None

        # Download the audio file
        out_file = video.download(output_path=settings.MEDIA_ROOT)
        print("Audio file downloaded.")

        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'

        # Convert mp4 to mp3 using pydub
        audio = AudioSegment.from_file(out_file)
        audio.export(new_file, format="mp3")
        print("Conversion to mp3 complete.")

        # Clean up the original mp4 file
        os.remove(out_file)
        print("Original mp4 file removed.")

        return new_file

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_transcription(link):
    try:
        # Call the function to download and convert the audio
        audio_file = download_audio(link)
        
        if audio_file:
            # Return the file path as a success response
            audio_file = download_audio(link)
            aai.settings.api_key = "fbd52160efc74801968e48bda1892107"
            
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_file)

            return transcript.text
        else:
            return JsonResponse({'error': 'Failed to download audio'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_article_from_transcription(transcription):
    openai.api_key = "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"

    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"
    response =  openai.completions.create(
        model="text-davinci-003",
        prompt =  prompt,
        max_tokens=1000,
    )
    generated_content = response.choices[0].text.strip()
    return generated_content

def user_login(request):
    if request.method=='POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username =  request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']
        
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('index')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})

        else:
            error_message = "Passwords do not match"
            return render(request, 'signup.html', {'error_message':error_message})
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('index')