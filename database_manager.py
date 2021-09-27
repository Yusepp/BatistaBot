import firebase_admin
from firebase_admin import credentials, firestore


class Playlist(object):


    def __init__(self,user,playlists = {}):
        self.user = user
        self.playlists = playlists
    

    @staticmethod
    def from_dict(source):
        if "user" not in source:
            raise Exception("Please Insert User.")
        else:
            return Playlist(**source)


    def to_dict(self):
        return { "user": self.user, "playlists": self.playlists }
    

    
class DB_Manager():


    def __init__(self,secret_json):
        self.cred = credentials.Certificate(secret_json)
        firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        self.playlists_ref = self.db.collection("playlists")
    
    
    def add_user(self, user, playlists = {}):
        try:
            self.playlists_ref.document(user).set(
                Playlist(user, playlists).to_dict()
            )

            return True

        except:
            return False
    

    def verify_credentials(self, user):
        try:
            query = self.playlists_ref.where('user', '==' , user).get()[0]
            user_data = query._data
            return user_data["user"] == user , user_data
        except:
            return False, {}
    

    def update_playlist(self,user,playlist_name,playlist_songs):
        status, data = self.verify_credentials(user)

        if status:
            try:
                self.playlists_ref.document(user).delete()
                data["playlists"][playlist_name] = playlist_songs
                self.add_user(**data)
                return True

            except Exception as e:
                print(e.args)
                return False
    

    def remove_playlist(self,user,playlist_name):
        status, data = self.verify_credentials(user)

        if status:
            self.playlists_ref.document(user).delete()
            del data['playlists'][playlist_name]
            self.add_user(**data)
        
        return status
    
    def get_playlists(self,user):
        status, data = self.verify_credentials(user)
        if status:
            return data["playlists"]
        else:
            return {}