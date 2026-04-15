import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Assistant", layout="wide")

st.title("📊 AI Business Reporting Assistant")
st.write("Smart insights for your marketing performance 🚀")

query = st.text_input("Ask your business question:")

if query:
    with st.spinner("Analyzing data..."):
        try:
            from orchestrator import Orchestrator

            orc = Orchestrator()
            result = orc.ask(query)

            # 🔹 Insight Section
            st.subheader("🧠 AI Insight")
            st.write(result["insight"])

            # 🔹 Convert analysis to DataFrame
            analysis = result["analysis"]

            if "ranked" in analysis:
                df = pd.DataFrame(analysis["ranked"])
                st.subheader("📊 Channel Performance")
                st.dataframe(df)

                st.subheader("📈 ROAS Comparison")
                st.bar_chart(df.set_index("channel")["roas"])

            elif "trend" in analysis:
                df = pd.DataFrame(analysis["trend"])
                st.subheader("📈 Monthly Trend")
                st.line_chart(df.set_index("month")[["revenue", "spend"]])

            else:
                df = pd.DataFrame(analysis["data"])
                st.subheader("📊 Data View")
                st.dataframe(df)

        except Exception as e:
            st.error(f"Error: {e}")

# Sidebar
st.sidebar.title("💡 Example Queries")
st.sidebar.write("• Which channel has the best ROAS?")
st.sidebar.write("• Show me monthly revenue trends")
st.sidebar.write("• Which campaigns are underperforming?")
st.sidebar.write("• Which product generates most revenue?")