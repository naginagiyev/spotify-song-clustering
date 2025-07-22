import os
import pickle
import openl3
from tqdm import tqdm
import soundfile as sf

embeddings_dict = {}
folder_path = "./songs"

for basename in tqdm(os.listdir(folder_path)[300:], desc="Getting Embeddings"):
    file_path = os.path.join(folder_path, basename)
    audio, sr = sf.read(file_path)
    embeddings, ts = openl3.get_audio_embedding(audio, sr, input_repr="mel256", content_type="music", embedding_size=512)
    embedding_vector = embeddings.mean(axis=0)
    embeddings_dict[basename] = embedding_vector

with open("./files/embedings.pkl", "wb") as f:
    pickle.dump(embeddings_dict, f)