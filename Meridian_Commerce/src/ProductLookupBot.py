
import os
import pandas as pd
import streamlit as st
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import anthropic


# UI Setup

st.set_page_config(
    page_title="Meridian Product Finder",
    page_icon="🔎",
    layout="wide"
)

load_dotenv()

# Load local retrieval resources

@st.cache_resource
def load_retrieval_resources():
    bi_encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    chroma_client = chromadb.PersistentClient("./chroma_db")
    collection = chroma_client.get_collection("meridian_products")

    return bi_encoder, cross_encoder, collection


@st.cache_resource
def load_claude_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key)


bi_encoder, cross_encoder, collection = load_retrieval_resources()
claude_client = load_claude_client()


# Data retrieval

def retrieve_and_rerank(query, initial_k=15, final_k=5):

    query_embedding = bi_encoder.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(initial_k, collection.count()),
        include=["documents", "embeddings", "metadatas"]
    )

    candidates = []

    cosine_scores = cosine_similarity(
        [query_embedding],
        results["embeddings"][0]
    )[0]

    for product_id, document, metadata, score in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        cosine_scores
    ):
        candidates.append({
            "product_id": product_id,
            "document": document,
            "metadata": metadata,
            "bi_encoder_score": float(score)
        })

    # Wide search results
    candidates = sorted(
        candidates,
        key=lambda x: x["bi_encoder_score"],
        reverse=True
    )

    # Reranking / Cross-encoding / Narrow search
    pairs = [
        [query, item["document"]]
        for item in candidates
    ]

    cross_scores = cross_encoder.predict(pairs)

    for item, score in zip(candidates, cross_scores):
        item["cross_encoder_score"] = float(score)

    reranked = sorted(
        candidates,
        key=lambda x: x["cross_encoder_score"],
        reverse=True
    )[:final_k]

    return reranked


# Retrieved, Augmentation & Generation

def generate_rag_response(query,hyde_query,chat_history, products):

    if claude_client is None:
        return (
            "The product search results are shown below. "
            "Claude is not configured because ANTHROPIC_API_KEY was not found."
        )

    context_parts = []

    #RETRIEVED
    for i, item in enumerate(products, start=1):
        context_parts.append(
            f"""
Product {i}
Name: {item['metadata']['product_name']}
SKU: {item['metadata']['sku']}
Category: {item['metadata']['category']}
Sub-category: {item['metadata']['sub_category']}
Brand: {item['metadata']['brand']}
Price: ₹{item['metadata']['price']:.2f}
Rating: {item['metadata']['avg_rating']}
Stock Status: {item['metadata']['stock_status']}
Catalog Details:
{item['document']}
"""
        )

    context = "\n---\n".join(context_parts)

    #AUGMENTATION
    prompt = f"""
You are the Meridian Commerce product discovery assistant.

A customer searched for:
"{query}"

Following is the LLM elaborated and optimized version of the above query:
"{hyde_query}"

Below are products retrieved from the catalog and reranked for relevance:

"{context}"

Below is the customer's chat history:
"{chat_history}"

Recommend the most relevant products based ONLY on the retrieved catalog context.

Instructions:
- Refer the LLM elaborated and optimized query for a better generated response; Any reference to any additional details from the optimized query should feel like natural assumption and must not indicate that the customer mentioned those details in the customer query explicitly.
- Explain briefly why the best matches fit the customer's request.
- Mention product names and SKU values.
- Do not invent product specifications.
- If no product is a strong match, say so clearly.
- Keep the answer concise and customer-friendly.
- However, if searched for product is unidentifiable then do not guess the product and clearly state the same politely.
- If the customer search does not relate to any product search query, politely prompt the customer towards product search.
- Refer the chat_history for relevance if required.
"""

    #GENERATION
    response = claude_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text




#HyDE query optimization
def generate_hyde_document(query, chat_history):
    
    prompt = f"""
You are helping improve semantic product search for an e-commerce product catalog.

A customer entered this search query:

"{query}"

Following is the previous chat_history of the chat:
"{chat_history}"

Generate a hypothetical product description that would ideally match
what the customer is looking for.
Consider the chat_history and refer to it only if the chat_history is relevant to the current customer query optimization.
Ignore the chat_history if it is not related to the current question.

Do not answer the customer.
Do not mention that this is hypothetical.
Do not recommend specific products.

Write a concise product-style description including likely relevant
features, use cases, and characteristics that would help semantic
search retrieve suitable products.

For the above situation, return only the hypothetical product description.


However, if searched for product is unidentifiable then do not guess the product and clearly quote just the product name
being looked for without any additional hypothetical description and just generate the product search query as a minimalistic search prompt
and return the same.
OR
If the customer query does not relate to any product search query, return the original customer query as it is without any modifications.
"""

    response = claude_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text
    



# Streamlit UI

st.title("🔎 Meridian Product Finder")

st.write(
    "Please describe what product you're looking for."
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Display previous chat messages
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])


# Get new user input
query = st.chat_input(
    "Example: I need comfortable shoes for running long distances"
)

if query:

    st.chat_message("user").write(query)
    hyde_query = generate_hyde_document(query, str(st.session_state.chat_history))

    # Store and user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": hyde_query
        }
    )

    with st.spinner("Searching the product catalog..."):
        products = retrieve_and_rerank(hyde_query)

    with st.spinner("Generating recommendations..."):
        answer = generate_rag_response(
            query,
            hyde_query,
            str(st.session_state.chat_history),
            products
        )

    # Store assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )
    # Persist actual conversation context for next query
    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": query
        }
    )

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    # Display assistant response
    st.chat_message("assistant").write(answer)