"""
Backs up and restores a settings file to Dropbox.
This is an example app for API v2.
"""

import sys
import dropbox
import os
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

# Add OAuth2 access token here.
# You can generate one for yourself in the App Console.
# See <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
TOKEN = ''

LOCALBACKUP = './file_backup/'
LOCALFILE = os.listdir(LOCALBACKUP)
BACKUPPATH = '/backup_server'
CHUNK_SIZE = 10 * 1024 * 1024

# Chunking uploads contents of LOCALFILE to Dropbox
def backup_chunk():
    for file in LOCALFILE:
        with open(LOCALBACKUP+file, 'rb') as f:
            file_size = os.path.getsize(LOCALBACKUP+file)
            if file_size <= CHUNK_SIZE:
                # We use WriteMode=overwrite to make sure that the settings in the file
                # are changed on upload
                print ("Uploading " + file + " to Dropbox as " + BACKUPPATH+'/'+file + "...")
                try:

                    dbx.files_upload(f, BACKUPPATH+'/'+file, mode=WriteMode('overwrite'))
                except ApiError as err:
                    # This checks for the specific error where a user doesn't have
                    # enough Dropbox space quota to upload this file
                    if (err.error.is_path() and
                            err.error.get_path().error.is_insufficient_space()):
                        sys.exit("ERROR: Cannot back up; insufficient space.")
                    elif err.user_message_text:
                        print(err.user_message_text)
                        sys.exit()
                    else:
                        print(err)
                        sys.exit()
            else:
                upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                           offset=f.tell())
                commit = dropbox.files.CommitInfo(path=BACKUPPATH+'/'+file)
                print ("Uploading " + file + " to Dropbox as " + BACKUPPATH+'/'+file + "...")
                while f.tell() < file_size:
                    if ((file_size - f.tell()) <= CHUNK_SIZE):
                        dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                        cursor,
                                                        commit)
                    else:
                        dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                        cursor.session_id,
                                                        cursor.offset)
                        cursor.offset = f.tell()

# Uploads contents of LOCALFILE to Dropbox
def backup():
    for file in LOCALFILE:
        with open(LOCALBACKUP+file, 'rb') as f:
            # We use WriteMode=overwrite to make sure that the settings in the file
            # are changed on upload
            print ("Uploading " + file + " to Dropbox as " + BACKUPPATH+'/'+file + "...")
            try:

                dbx.files_upload(f, BACKUPPATH+'/'+file, mode=WriteMode('overwrite'))
            except ApiError as err:
                # This checks for the specific error where a user doesn't have
                # enough Dropbox space quota to upload this file
                if (err.error.is_path() and
                        err.error.get_path().error.is_insufficient_space()):
                    sys.exit("ERROR: Cannot back up; insufficient space.")
                elif err.user_message_text:
                    print(err.user_message_text)
                    sys.exit()
                else:
                    print(err)
                    sys.exit()

if __name__ == '__main__':
    # Check for an access token
    if (len(TOKEN) == 0):
        sys.exit("ERROR: Looks like you didn't add your access token. Open up backup-and-restore-example.py in a text editor and paste in your token in line 14.")

    # Create an instance of a Dropbox class, which can make requests to the API.
    print("Creating a Dropbox object...")
    dbx = dropbox.Dropbox(TOKEN)

    # Check that the access token is valid
    try:
        dbx.users_get_current_account()
    except AuthError as err:
        sys.exit("ERROR: Invalid access token; try re-generating an access token from the app console on the web.")

    # Delete backup folder first
    print("Deleting backup folder on dropbox first...")
    try:
        dbx.files_delete(BACKUPPATH)
    except:
        pass

    # Create a backup of the current settings file
    backup_chunk()

    print("Done!")
