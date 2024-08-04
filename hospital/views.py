from django.shortcuts import render,redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, TemplateView
from .models import Doctor
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.http import HttpResponse
import os
import base64
from django.conf import settings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("Client ID:", os.getenv('GOOGLE_OAUTH2_CLIENT_ID'))
print("Client Secret:", os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET'))
print("Redirect URI:", os.getenv('GOOGLE_OAUTH2_REDIRECT_URI'))

# Make sure your settings are correctly configured
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class hospitalView(TemplateView):
    template_name = 'index.html'


class DoctorListView(ListView):
    queryset = Doctor.objects.all()
    template_name = 'doctor-team.html'



class ContactView(TemplateView):
    template_name = 'contact.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            name = request.POST.get('name')
            email_from  = request.POST.get('email')
            subject = request.POST.get('subject', '')  # Default to empty string if not provided
            message = request.POST.get('message', '')  # Default to empty string if not provided

            if subject == '':
                subject = 'Healthcae Contact'     

            if name and email_from and message:
                try:
                    flow = Flow.from_client_config(
                        {
                            "web": {
                                "client_id": os.getenv('GOOGLE_OAUTH2_CLIENT_ID'),
                                "client_secret": os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET'),
                                "redirect_uris": [os.getenv('GOOGLE_OAUTH2_REDIRECT_URI')],
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                            }
                        },
                        scopes=SCOPES
                    )
                    flow.redirect_uri = request.build_absolute_uri('/oauth2callback/')
                    authorization_url, state = flow.authorization_url(
                        access_type='offline',
                        include_granted_scopes='true'
                    )
                    request.session['state'] = state
                    request.session['name'] = name
                    request.session['email_from'] = email_from
                    request.session['subject'] = subject
                    request.session['message'] = message
                    return redirect(authorization_url)
                except Exception as e:
                    messages.error(request, f'Something went wrong: {str(e)}')
            else:
                messages.error(request, 'Please fill out all required fields.')

            return redirect('contact')
        
def oauth2callback(request):
    state = request.session['state']
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv('GOOGLE_OAUTH2_CLIENT_ID'),
                "client_secret": os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET'),
                "redirect_uris": [os.getenv('GOOGLE_OAUTH2_REDIRECT_URI')],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
            }
        },
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = request.build_absolute_uri('/oauth2callback/')
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)

    name = request.session['name']
    email_from = request.session['email_from']
    subject = request.session['subject']
    message = request.session['message']

    try:
        service = build('gmail', 'v1', credentials=credentials)
        email_message = {
            'raw': base64.urlsafe_b64encode(
                f"To: {os.getenv('EMAIL_RECIPIENT')}\nSubject: {subject} - {name}\n\n{message}\n\nFrom: {email_from}".encode('utf-8')
            ).decode('utf-8')
        }
        service.users().messages().send(userId='me', body=email_message).execute()
        messages.success(request, f'Your message has been sent. Thank you {name}!')
    except Exception as e:
        messages.error(request, f'Something went wrong: {str(e)}')

    return redirect('contact')

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }