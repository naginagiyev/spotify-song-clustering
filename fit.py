import pickle
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score

with open("./files/embeddings.pkl", "rb") as f:
    df = pickle.load(f)

X = df.iloc[:, 1:].values
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

pca = PCA(n_components=0.58, random_state=42)
X_pca = pca.fit_transform(X_scaled)

clusterer = KMeans(n_clusters=4, random_state=42)
labels = clusterer.fit_predict(X_pca)
df["cluster"] = labels

mask = labels != -1
if len(set(labels)) > 1:
    sil_score = silhouette_score(X_pca[mask], labels[mask])
    db_score = davies_bouldin_score(X_pca[mask], labels[mask])
else:
    sil_score = float('nan')
    db_score = float('nan')

print(f"✅ Silhouette Score: {sil_score:.4f}")
print(f"✅ Davies-Bouldin Score: {db_score:.4f}")

df["x"] = X_pca[:, 0]
df["y"] = X_pca[:, 1]

final_df = df[[df.columns[0], "x", "y", "cluster"]].copy()
final_df.columns = ["cover", "x", "y", "cluster"]
final_df["cover"] = final_df["cover"].str.replace(".wav", ".png", regex=False)
final_df["title"] = final_df["cover"].str.replace(".png", "", regex=False)

def smart_title(text):
    return ' '.join(word.capitalize() if word.lower() != "by" else "by" for word in text.split())

final_df["title"] = final_df["title"].apply(smart_title)

with open("song_clusters.pkl", "wb") as f:
    pickle.dump(final_df, f)