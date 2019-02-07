# -*- coding: gql -*-

GET_FILM = gql'''
    query GetFilm($theFilmID: ID!) {
      film(id: $theFilmID) {
        title
        director
      }
    }
'''

GET_FILM.execute('ZmlsbXM6MQ==')
