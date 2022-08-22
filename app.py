from flask import Flask, session, request, render_template, url_for, redirect
from spotipy.oauth2 import SpotifyOAuth
import dotenv
import spotipy
import os

dotenv.load_dotenv(dotenv.find_dotenv())

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_COOKIE_NAME'] = 'User cookie'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    sp_oauth = create_spotipy_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/authorize')
def authorize():
    sp_oauth = create_spotipy_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect('/playlists')

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/playlists', methods=['GET', 'POST'])
def playlists():
    sp = spotipy.Spotify(auth=session['token_info']['access_token'])
    
    # Consultando as Playlists
    results = sp.current_user_playlists()
    playlist_info = []
    for playlist in results['items']:
            playlist_info.append([playlist['id'], playlist['name']])
  
    return render_template('playlists.html', **{'playlist_info': playlist_info})

@app.route('/playlist-created', methods=['POST'])
def create_playlist():
    sp = spotipy.Spotify(auth=session['token_info']['access_token'])
    user = sp.current_user()['id']
    
    if request.method == 'POST':
        list_of_songs = []
        list_of_songs.clear()
        
        for i in request.form:
            # Ajustando o ID com fatiamento de strings
            if i != 'playlist_name':
                playlist_id = i.split(',')[0][2:-1:]
            
                # Acessando as Músicas e adicionando em uma lista
                track = sp.playlist_items(playlist_id=playlist_id)
                for music in track['items']:
                    list_of_songs.append(music["track"]["uri"])

        playlist_list1 = []
        playlist_list2 = []
        name = request.form.get('playlist_name')
        user_playlists = sp.current_user_playlists()
     
        # Consultando as playlists   
        for i in user_playlists['items']:
            playlist_list1.append({'id': i['id'], 'playlist_name': i['name']})
        
        for i in playlist_list1:
            if i.get('playlist_name') == name:
                # Adicionando as músicas em uma playlist que o usuário já possui
                playlist_id = i.get('id')
                sp.user_playlist_add_tracks(user=user, playlist_id=playlist_id, tracks=list_of_songs)
                return render_template('playlist-created.html')
    
        # Criando playlist caso ainda não exista
        sp.user_playlist_create(user=user, name=name, public=True)
        
        # Atualizando a lista de playlists
        user_playlists = sp.current_user_playlists()
        for i in user_playlists['items']:
            playlist_list2.append({'id': i['id'], 'playlist_name': i['name']})
        
        for i in playlist_list2:
            if i.get('playlist_name') == name:
                # Adicionando as músicas em uma playlist que o usuário criou agora
                playlist_id = i.get('id')
                sp.user_playlist_add_tracks(user=user, playlist_id=playlist_id, tracks=list_of_songs)
                return render_template('playlist-created.html')
            
    else:
        return render_template('playlists.html')
        
    return render_template('playlist-created.html')

def create_spotipy_oauth():
    return SpotifyOAuth(client_id=os.getenv('client_id'),
            client_secret=os.getenv('client_secret'),
            redirect_uri=url_for('authorize', _external=True),
            scope='user-library-read playlist-modify-public')