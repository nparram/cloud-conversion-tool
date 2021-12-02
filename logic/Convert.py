# import library
from pydub import AudioSegment
import os

class Convert:

    def convert_generic(self, orig_song, dest_song):
        os.system('ffmpeg -loglevel %s -i \"%s\"  \"%s\"' % ('fatal', orig_song, dest_song))

    def convert_mp3_to_wav(self, orig_song, dest_song):
        song = AudioSegment.from_mp3(orig_song)
        song.export(dest_song, format="wav")

    def convert_mp3_to_wma(self, orig_song, dest_song):
        os.system('ffmpeg -loglevel %s -i \"%s\" -acodec libmp3lame \"%s\"' % ('fatal', orig_song, dest_song))

    def convert_mp3_to_wav(self, orig_song, dest_song):
        song = AudioSegment.from_mp3(orig_song)
        song.export(dest_song, format="wav")

    # OGG Files
    def convert_ogg_to_wav(self, orig_song, dest_song):
        song = AudioSegment.from_ogg(orig_song)
        song.export(dest_song, format="wav")

    def convert_ogg_to_mp3(self, orig_song, dest_song):
        song = AudioSegment.from_ogg(orig_song)
        song.export(dest_song, format="mp3")

    # WAV Files
    def convert_wav_to_mp3(self, orig_song, dest_song):
        song = AudioSegment.from_wav(orig_song)
        song.export(dest_song, format="mp3")

    def convert_wav_to_ogg(self, orig_song, dest_song):
        song = AudioSegment.from_wav(orig_song)
        song.export(dest_song, format="ogg")

    def convert_wav_to_ogg(self, orig_song, dest_song):
        song = AudioSegment.from_wav(orig_song)
        song.export(dest_song, format="ogg")

# MP3 - ACC - OGG - WAV – WMA
