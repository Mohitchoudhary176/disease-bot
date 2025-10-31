import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

st.title("Disease Bot")
st.write("Ask any question about symptoms or diseases.")

# User input box
user_input = st.text_input("Enter your question here:")

# Only call API if user typed something
if user_input:
    try:
        # Call OpenAI chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a medical helper. Provide safe, helpful, non-diagnostic advice."},
                {"role": "user", "content": user_input}
            ]
        )

        # ✅ NEW response format (replaces old message["content"])
        bot_reply = response.choices[0].message.content

        st.write("### 🤖 Bot Reply:")
        st.write(bot_reply)

    except Exception as e:
        st.error("Something went wrong while contacting OpenAI API.")
        st.exception(e)












