import streamlit as st
import pickle
import pandas as pd
import requests
import bz2
import os

# TMDB API key
TMDB_API_KEY = "d292716455cac395c3a09fe1de860315"

# Fetch TMDB movie ID
def fetch_movie_id(title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    response = requests.get(url)
    data = response.json()
    results = data.get('results')
    if results:
        return results[0]['id']
    return None

# Fetch movie details
def fetch_movie_details(movie_id):
    response = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    )
    data = response.json()

    poster_url = "https://image.tmdb.org/t/p/w500/" + data['poster_path'] if data.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Image"
    overview = data.get('overview', 'No description available.')
    release_year = data.get('release_date', 'Unknown')[:4] if data.get('release_date') else 'Unknown'
    rating = data.get('vote_average', 'N/A')

    trailer_url = None
    video_response = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=en-US"
    )
    video_data = video_response.json()
    results = video_data.get('results', [])
    for video in results:
        if video['site'] == 'YouTube' and video['type'] == 'Trailer':
            trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
            break

    return poster_url, overview, release_year, rating, trailer_url

# Recommend function
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    posters = []
    overviews = []
    years = []
    ratings = []
    trailers = []

    for i in movie_list:
        title = movies.iloc[i[0]].title
        recommended_movies.append(title)

        movie_id = fetch_movie_id(title)
        if movie_id:
            poster, overview, year, rating, trailer = fetch_movie_details(movie_id)
        else:
            poster = "https://via.placeholder.com/500x750?text=No+Image"
            overview = "No description available."
            year = "Unknown"
            rating = "N/A"
            trailer = None

        posters.append(poster)
        overviews.append(overview)
        years.append(year)
        ratings.append(rating)
        trailers.append(trailer)

    return recommended_movies, posters, overviews, years, ratings, trailers

# Load data
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

# Fix filename if needed
if os.path.exists('similarity.pkl.gz2'):
    os.rename('similarity.pkl.gz2', 'similarity.pkl.bz2')

# Load compressed similarity matrix
with bz2.BZ2File('similarity.pkl.bz2', 'rb') as f:
    similarity = pickle.load(f)

# App UI
st.title('🎬 Movie Recommender System')

selected_movie_name = st.selectbox(
    'Select a movie to get recommendations:',
    movies['title'].values
)

# Initialize session states
if 'last_selected_movie' not in st.session_state:
    st.session_state.last_selected_movie = None
if 'active_info_index' not in st.session_state:
    st.session_state.active_info_index = None

# Recommend button
if st.button('Recommend'):
    if st.session_state.last_selected_movie != selected_movie_name:
        st.session_state.last_selected_movie = selected_movie_name
        st.session_state.active_info_index = None  # reset active info
    st.session_state.show_recommendations = True

# Show recommendations
if st.session_state.get('show_recommendations', False):
    names, posters, overviews, years, ratings, trailers = recommend(selected_movie_name)

    for i in range(5):
        st.markdown("----")
        st.subheader(f"🎞 {names[i]}")

        # Show Info button
        if st.button("Show Info", key=f'info_btn_{i}'):
            # If clicking same index again -> toggle off
            if st.session_state.active_info_index == i:
                st.session_state.active_info_index = None
            else:
                st.session_state.active_info_index = i

        if st.session_state.active_info_index == i:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(posters[i], width=200)
            with col2:
                st.markdown(f"*Year:* {years[i]}")
                st.markdown(f"*Rating:* ⭐ {ratings[i]}")
                st.markdown(f"*Overview:* {overviews[i]}")
                if trailers[i]:
                    st.markdown(f"[🎬 Watch Trailer]({trailers[i]})", unsafe_allow_html=True)
