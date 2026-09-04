import os
import re
import pickle
from pathlib import Path

import faiss
import streamlit as st
import anthropic
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder

st.set_page_config(page_title="Meridian Customer Support", page_icon="💬", layout="wide")


load_dotenv()


@st.cache_resource
def load_retrieval_resources():
    bi_encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    index = faiss.read_index('./faiss_policy_index/policy.index')

    with open('./faiss_policy_index/policy_chunks.pkl', "rb") as f:
        policy_chunks = pickle.load(f)

    return bi_encoder, cross_encoder, index, policy_chunks


@st.cache_resource
def load_claude_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY was not found. Add it to the .env file."
        )

    return anthropic.Anthropic(api_key=api_key)


@st.cache_data
# Loading FAQs
def load_faq_cache(file_path):

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"FAQ file not found: {file_path}"
        )

    text = file_path.read_text(
        encoding="utf-8"
    ).strip()

    cache = {}

    # Normalize line endings
    text = text.replace("\r\n", "\n")

    # Split whenever a new FAQ question begins.
    # (?m) allows ^Q: to match at the beginning of every line.
    faq_blocks = re.split(
        r"(?m)^\s*Q:\s*",
        text
    )

    for block in faq_blocks:

        block = block.strip()

        if not block:
            continue

        # Split the block into question and answer
        parts = re.split(
            r"(?m)^\s*A:\s*",
            block,
            maxsplit=1
        )

        # Skip malformed blocks
        if len(parts) != 2:
            continue

        question = parts[0].strip()
        answer = parts[1].strip()

        # Convert multi-line question/answer into clean single strings
        question = " ".join(
            line.strip()
            for line in question.splitlines()
            if line.strip()
        )

        answer = " ".join(
            line.strip()
            for line in answer.splitlines()
            if line.strip()
        )

        if question and answer:
            cache[question] = answer

    if not cache:
        raise ValueError(
            "No FAQs could be parsed. "
            "Expected format:\n"
            "Q: question\n"
            "A: answer"
        )

    return cache


bi_encoder, cross_encoder, index, policy_chunks = load_retrieval_resources()
claude_client = load_claude_client()
faq_cache = load_faq_cache('./resources/CustomerSupportData/policy_payment_refunds_faq.txt')


def generate_hyde_document(query, chat_history):
    prompt = f'''
You are helping improve semantic retrieval for a Meridian Commerce customer-support policy knowledge base.

Customer question:
"{query}"

Previous chat history:
"{chat_history}"

Generate a short hypothetical policy passage that would ideally contain the information needed to answer the customer's current question.

Consider previous chat history only when relevant. Use it to resolve follow-up references such as "that", "it", "this", or "what about that".

Do not answer the customer.
Do not mention that this is hypothetical.
Do not invent Meridian Commerce policy details.

Write in neutral policy/document style with relevant conditions, exceptions, thresholds, and terminology.

Return only the retrieval-optimized hypothetical policy passage.
'''

    response = claude_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=250,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text.strip()


def retrieve_and_rerank(query, initial_k=10, final_k=4):
    query_embedding = bi_encoder.encode(
        [query],
        convert_to_numpy=True
    ).astype("float32")

    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(
        query_embedding,
        min(initial_k, index.ntotal)
    )

    candidates = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        item = policy_chunks[int(idx)].copy()
        item["bi_encoder_score"] = float(score)
        candidates.append(item)

    pairs = [
        (query, item["text"])
        for item in candidates
    ]

    cross_scores = cross_encoder.predict(pairs)

    for item, score in zip(candidates, cross_scores):
        item["cross_encoder_score"] = float(score)

    return sorted(
        candidates,
        key=lambda x: x["cross_encoder_score"],
        reverse=True
    )[:final_k]


def generate_rag_response(query, hyde_query, chat_history, retrieved_chunks):
    context = "\n---\n".join(
        f"Source: {item.get('source', 'Policy document')}\n{item['text']}"
        for item in retrieved_chunks
    )

    prompt = f'''
You are the Meridian Commerce customer support assistant.

Customer's current question:
"{query}"

Retrieval-optimized version of the question:
"{hyde_query}"

Previous chat history:
"{chat_history}"

Retrieved and reranked policy context:
"{context}"

Answer using ONLY the retrieved policy context.

Instructions:
- Use previous chat history when relevant to understand follow-up questions.
- Apply the most specific policy to the customer's situation.
- If a policy contains an exception or override, it takes precedence over a general rule.
- Do not invent policies, dates, monetary amounts, thresholds, eligibility rules, or exceptions.
- Do not use outside knowledge.
- Do not mention HyDE, FAISS, embeddings, reranking, retrieved chunks, or internal systems.
- Do not expose the optimized query.
- If the retrieved context is insufficient, clearly say so.
- Keep the answer concise, clear, and customer-friendly.
'''

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

    return response.content[0].text.strip()


if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


st.title("💬 Meridian Customer Support")
st.write(
    "Ask questions about orders, returns, shipping, payments, warranty, and Meridian Commerce policies."
)


with st.sidebar:
    st.header("Frequently Asked Questions")
    st.caption("Select a question for an instant cached answer.")

    selected_faq = None

    for i, question in enumerate(faq_cache.keys()):
        if st.button(
            question,
            key=f"faq_{i}",
            use_container_width=True
        ):
            selected_faq = question


for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])


if selected_faq:
    faq_answer = faq_cache[selected_faq]

    st.session_state.messages.append(
        {
            "role": "user",
            "content": selected_faq
        }
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": faq_answer
        }
    )

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": selected_faq
        }
    )

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": faq_answer
        }
    )

    st.rerun()


query = st.chat_input(
    "Ask a question about your order or Meridian Commerce policies..."
)


if query:
    st.chat_message("user").write(query)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query
        }
    )

    chat_history_text = str(st.session_state.chat_history)

    with st.spinner("Understanding your question..."):
        hyde_query = generate_hyde_document(
            query,
            chat_history_text
        )

    with st.spinner("Searching Meridian Commerce policies..."):
        retrieved_chunks = retrieve_and_rerank(
            hyde_query
        )

    with st.spinner("Preparing your answer..."):
        answer = generate_rag_response(
            query,
            hyde_query,
            chat_history_text,
            retrieved_chunks
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

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

    st.chat_message("assistant").write(answer)
