import os
from groq import Groq
import pandas as pd
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import streamlit as st
from pathlib import Path

# Initialize Groq API key
lama_new = "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"

# Create necessary directories
def setup_directories():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data')
    db_dir = os.path.join(current_dir, 'chroma_db')
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)
    
    return data_dir, db_dir

# Step 1: Preprocess Dataset and Generate Sentences
@st.cache_data
def preprocess_and_generate_sentences(data_path):
    try:
        dataset = pd.read_csv(data_path)
        dataset.columns = dataset.columns.str.strip()
        dataset = dataset.fillna("")
        
        sentences = []
        for _, row in dataset.iterrows():
            sentence = (
                f"In {row['Place and Country']}, you can visit attractions like {row['Attractions']}. "
                f"Enjoy dining at restaurants such as {row['Restaurants']}. Cultural activities include {row['Cultural Activities']}. "
                f"For outdoor activities, you can experience {row['Outdoor Activities']}. "
                f"Don't miss out on food and beverage options like {row['Food and Beverage']}. "
                f"Budget-friendly options include accommodations at {row['Budget-Friendly Options (Est. Price)']}. "
                f"Midrange options are {row['Midrange Options (Est. Price)']}, while luxury options include stays at {row['Luxury Options (Est. Price)']}. "
                f"The estimated cost per day ranges from {row['Estimated Cost']}."
            )
            sentences.append(sentence)
        return sentences, dataset
    except FileNotFoundError:
        st.error(f"Dataset file not found at {data_path}. Please ensure the CSV file is in the correct location.")
        return None, None
    except Exception as e:
        st.error(f"Error processing dataset: {str(e)}")
        return None, None

# Initialize ChromaDB and Collection (combined to avoid caching issues)
@st.cache_resource
def initialize_chroma_and_collection(db_dir):
    try:
        # Initialize ChromaDB
        settings = Settings(
            persist_directory=db_dir,
            chroma_db_impl="duckdb+parquet"
        )
        client = chromadb.PersistentClient(path=db_dir)
        
        # Initialize embedding function
        embedding_function = SentenceTransformerEmbedding()
        
        # Initialize collection
        collection_name = "travel_itineraries_lama"
        if collection_name in [c.name for c in client.list_collections()]:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=embedding_function
            )
        else:
            collection = client.create_collection(
                name=collection_name,
                embedding_function=embedding_function
            )
        
        return client, collection
    except Exception as e:
        st.error(f"Error initializing ChromaDB and collection: {str(e)}")
        return None, None

class SentenceTransformerEmbedding:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        embeddings = self.model.encode(input, convert_to_tensor=False)
        return embeddings.tolist()

def retrieve_from_chroma(collection, query_text, top_n=5):
    try:
        results = collection.query(query_texts=[query_text], n_results=top_n)
        retrieved_docs = [doc[0] for doc in results["documents"]]
        return retrieved_docs
    except Exception as e:
        st.error(f"Error retrieving from ChromaDB: {str(e)}")
        return None

def generate_itinerary(user_query, retrieved_docs):
    context = "\n".join(retrieved_docs)
    prompt = (
        "You are a highly knowledgeable Travel Itinerary Generator. "
        "Your goal is to provide personalized travel itineraries based on user preferences, including destinations, activities, and budget. "
        "I will provide you with context that includes detailed travel information and user-specific queries. "
        "You need to analyze this context to generate a comprehensive itinerary.\n\n"
        "Context: {context}\n"
        "Query: {query}\n\n"
        "Your tasks include:\n"
        "1. Understand the user's preferences and constraints from the query.\n"
        "2. Retrieve relevant travel information based on the provided context.\n"
        "3. Generate a detailed travel itinerary that includes recommended attractions, activities, dining options, accommodations, and estimated costs.\n"
        "4. Ensure the itinerary aligns with the user's budget and preferences.\n"
        "5. If the number of travel days is significant, but the context information is limited, enhance the itinerary by:\n"
        "   a. Including nearby cities, landmarks, or attractions known to you.\n"
        "   b. Suggesting additional activities or experiences based on the general travel region.\n"
        "   c. Providing options for day trips or excursions to maximize the travel experience.\n\n"
        "Please provide a detailed and personalized travel itinerary for the given query."
    ).format(context=context, query=user_query)

    try:
        client = Groq(api_key=lama_new)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error during API call: {str(e)}")
        return None

def main():
    st.title("Travel Itinerary Generator")
    st.write("Enter your travel preferences and get a personalized itinerary!")
    
    # Setup directories
    data_dir, db_dir = setup_directories()
    
    # Check for dataset file
    data_path = os.path.join(data_dir, '50_famous_destinations.csv')
    if not os.path.exists(data_path):
        st.error(f"""
        Dataset file not found at {data_path}
        Please ensure you have placed the '50_famous_destinations.csv' file in the 'data' folder.
        """)
        st.stop()
    
    # Initialize components
    sentences, dataset = preprocess_and_generate_sentences(data_path)
    if sentences is None:
        st.stop()
    
    # Initialize ChromaDB and collection together
    client, collection = initialize_chroma_and_collection(db_dir)
    if collection is None:
        st.stop()
    
    # Store data in ChromaDB if not already stored
    if not collection.get()["ids"]:
        try:
            collection.add(
                documents=sentences,
                metadatas=[{"index": idx} for idx in range(len(sentences))],
                ids=[f"doc_{idx}" for idx in range(len(sentences))]
            )
            st.success("Data successfully stored in ChromaDB!")
        except Exception as e:
            st.error(f"Error storing data in ChromaDB: {str(e)}")
            st.stop()
    
    # User input
    user_query = st.text_area(
        "Enter your travel query (e.g., '5-day trip to Paris with a medium budget'):",
        height=100
    )
    
    if st.button("Generate Itinerary"):
        if user_query:
            with st.spinner("Generating your personalized itinerary..."):
                retrieved_docs = retrieve_from_chroma(collection, user_query)
                
                if retrieved_docs:
                    itinerary = generate_itinerary(user_query, retrieved_docs)
                    if itinerary:
                        st.success("Your itinerary has been generated!")
                        st.markdown(itinerary)
                    else:
                        st.error("Failed to generate itinerary. Please try again.")
                else:
                    st.warning("No relevant results found in the database.")
        else:
            st.warning("Please enter a travel query first.")

if __name__ == "__main__":
    main()
