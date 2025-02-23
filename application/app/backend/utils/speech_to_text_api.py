from google.cloud import speech, storage
import wave
import sndhdr
import io
from pydub import AudioSegment


def get_sample_rate(path):
    """Finds the sample rate of an audio file

    Args:
        path: the path to the audio file

    Returns:
        The sample rate of the file
    """
    # Find the sample rate if the it's a GCS file
    if path.startswith("gs://"):
        bucket_name, blob_name = path[5:].split("/", 1)

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        audio_bytes = blob.download_as_bytes()
        with wave.open(io.BytesIO(audio_bytes), "rb") as audio_file:
            sample_rate = audio_file.getframerate()
            return sample_rate
    # Find the sample rate using sndhdr if it's a local file
    else:
        sample_rate = sndhdr.what(path).framerate
        return sample_rate

def split_audio(path):
    """Splits a 2-channel audio (stereo audio) into two 1-channel audios (mono audios)

    This functions breaks a stereo audio into two mono audios to keep the best quality of the original audio.

    NOTE: This function is not invoked at all yet, but might be relevant in the future for further development

    Args:
        path: The path to the audio file

    Returns:
        The list of mono audios
    """
    audio = AudioSegment.from_file(path)

    # Split the original 2-channel audio into two 1-channel audios
    channels = audio.split_to_mono()

    transcriptions = []
    # Store the 1-channel audios
    for i, channel in enumerate(channels):
        temp_path = f"channel_{i+1}.wav" # The path where the 1-channel audios will be stored
        channel.export(temp_path, format="wav")

        client = speech.SpeechClient()
        with open(temp_path, "rb") as audio_file:
            content = audio_file.read()
            audio_data = speech.RecognitionAudio(content=content)

            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=channel.frame_rate,
                language_code="en-US",
            )

            response = client.recognize(config=config, audio=audio_data)
            transcription = " ".join([result.alternatives[0].transcript for result in response.results])
            transcriptions.append(transcription)

    return transcriptions


def transcribe(path) -> speech.RecognizeResponse:
    """Transcribes an audio file to text

    This function recognizes an audio file and converts it to text using the Google Cloud Speech-to-text API

    Args:
        path: The path to the audio file

    Returns:
        A list containing texts converted from the given audio file

    """
    client = speech.SpeechClient()

    # if the file is on GCS, it can be recognized directly via the uri. 2-channel-audios cannot be recognized,
    # however, there is no way (found yet) to determine if a GCS audio has 2 channels.
    if path.startswith("gs://"):
        audio = speech.RecognitionAudio(uri=path)

    # if it's a local file, it must be read firstly before being recognized
    else:
        # if the local file has two channels, convert it to a mono-audio aka 1-channel audio
        if sndhdr.what(path).nchannels > 1:
            audio = AudioSegment.from_file(path)
            audio = audio.set_channels(1)
            # Replace the 2-channel audio with the 1-channel audio at the same location
            audio.export(path, format = "wav")

        with open(path, "rb") as file:
            content = file.read()

        audio = speech.RecognitionAudio(content=content)

    # find the individual sample rate of the audio
    rate = get_sample_rate(path)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=rate,
        language_code="de-DE",
    )

    response = client.recognize(config=config, audio=audio)

    transcription = []
    for result in response.results:
        transcription.append(result.alternatives[0].transcript)

    return transcription
