import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

try:
    cred = credentials.Certificate("D:/code/python/frc-scouting-app-data-viewer/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except FileNotFoundError:
    print("Error: Service account key file not found.")
    print(
        "Please download your service account key from the Firebase Console and update the file path."
    )
    exit()
except ValueError as e:
    print(f"Error initializing Firebase: {e}")
    exit()


db = firestore.client()


def fetch_collection_data(collection_name):
    print(f"/n--- Fetching data from collection: '{collection_name}' ---")
    try:
        collection_ref = db.collection(collection_name)
        # Get all documents
        docs = collection_ref.stream()

        data = {}
        for doc in docs:
            # doc.id is the document ID, doc.to_dict() is the data
            data[doc.id] = doc.to_dict()
            print(f"Fetched document ID: {doc.id}")

        return data

    except Exception as e:
        print(f"An error occurred during fetching: {e}")
        return None


# --- 4. Main execution ---
if __name__ == "__main__":
    # Replace "your_collection_name" with your actual Firestore collection name
    collection_name = "your_collection_name"
    all_data = fetch_collection_data(collection_name)

    if all_data is not None:
        # Print the data neatly as JSON
        print("/n--- All Data Fetched (JSON Output) ---")
        print(json.dumps(all_data, indent=4))
