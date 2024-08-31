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
from .models import Article
from dotenv import load_dotenv


# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

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
        
        #get transcript
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': 'Failed to get transcript'}, status=500)
        
        #use OpenAI to generate the article
        article_content = generate_article_from_transcription(transcription)
        if not article_content:
            return JsonResponse({'error': 'Failed to generate article'}, status=500)
        
        #save article to database
        new_article =Article.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=yt_link,
            generated_content=article_content,
        )
        new_article.save()
        
        #return article as response
        return JsonResponse({'content': article_content})
        
    else:
        return JsonResponse({'error':'Invalid request method'}, status=405)

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):

    try:
        yt = YouTube(link)
        print(f"Video Title: {yt.title}")

        streams = yt.streams.filter(only_audio=True)
        print(f"Available audio streams: {streams}")
        
        video = streams.first()

        if not video:
            print("No audio streams available.")
            return None

        out_file = video.download(output_path=settings.MEDIA_ROOT)
        print("Audio file downloaded.")

        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp3'
        os.rename(out_file, new_file)
        return new_file

    except Exception as e:
        print(f"An error occurred while downlading audio: {e}")
        return None


def get_transcription(link):
    try:
        audio_file = download_audio(link)
        
        if audio_file:
            load_dotenv()
            aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')

            
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_file)

            return transcript.text
        else:
            return JsonResponse({'error': 'Failed to download audio'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_article_from_transcription(transcription):
    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API_KEY')

    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"
    response =  openai.completions.create(
        model="gpt-3.5-turbo-0125",
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

def article_list(request):
    article_posts = Article.objects.filter(user=request.user)
    return render(request, "all-articles.html", {'article_posts':article_posts})

def article_details(request, pk):
    article_posts_details=Article.objects.get(id=pk)
    if request.user == article_posts_details.user:
        return render(request, 'article-details.html', {'article_posts_details':article_posts_details})
    else:
        return redirect('index')

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