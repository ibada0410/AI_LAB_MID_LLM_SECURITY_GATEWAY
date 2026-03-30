**Submitted for CSC 262 Lab Mid**

**Project Title :** LLM Security Gateway

**Submitted To :** Instructor: Tooba Tehreem

**Submitted By :** Ibad Ahmed

**Registration # :** FA24-BCS-209

**Section :** 4b





**Project Description**

Secure gateway that protects LLMs from prompt injection, jailbreaks, and PII leakage using FastAPI + Microsoft Presidio.



**Features**

\- Injection detection with scoring mechanism

\- Presidio with 3 customizations (Custom Recognizer, Context-aware scoring, Composite entity)

\- Configurable policy: Allow / Mask / Block

\- Basic latency measurement

\- 5 evaluation tables



**Installation \& Environment Setup**

1\. git clone https://github.com/ibada0410/AI\_LAB\_MID\_LLM\_SECURITY\_GATEWAY.git

2\. python -m venv venv

3\. venv\\Scripts\\activate

4\. pip install -r requirements.txt

5\. python -m spacy download en\_core\_web\_lg



**How to Run the Gateway**

uvicorn app.main:app --reload



**How to Reproduce Evaluation Results**

1\. Start server in one terminal: uvicorn app.main:app --reload

2\. Open second terminal and run:

&#x20;  cd tests

&#x20;  python run\_eval.py

Results saved in eval\_results/evaluation\_results.csv



**System Architecture**

!\[Architecture Diagram](docs/architecture\_diagram.png)



**GitHub Link:** https://github.com/ibada0410/AI\_LAB\_MID\_LLM\_SECURITY\_GATEWAY

**Demo Video:** (will be added after recording)





