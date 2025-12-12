# 🍽️ Automation of Restaurant Reservations with AI on WhatsApp & Google Sheets

![Made with n8n](https://img.shields.io/badge/Made%20with-n8n-blue?logo=n8n)
![LangChain](https://img.shields.io/badge/Powered%20by-LangChain-orange)
![OpenAI](https://img.shields.io/badge/AI-OpenAI-green)
![Google Sheets](https://img.shields.io/badge/CRM-Google%20Sheets-yellow)

## 📖 Overview
This project is an **n8n workflow** that automates restaurant reservations through **WhatsApp** using an **AI agent**.  
It guides customers through booking, calculates discounts based on bank cards, and logs reservations into **Google Sheets CRM** for easy management.

---

## ✨ Features
- **WhatsApp Integration**: Customers interact directly via WhatsApp messages.  
- **AI Agent**: Handles reservations, discount calculations, and FAQs.  
- **Google Sheets CRM**: Logs reservations with details like name, phone, date, slot timings, and status.  
- **Discount Calculator**: Applies bank card discounts with caps and tax rules.  
- **Automated Notifications**: Confirms or rejects reservations via WhatsApp.  

---

## 🛠️ Tech Stack
- [n8n](https://n8n.io/) – workflow automation  
- [LangChain](https://www.langchain.com/) – AI agent + memory  
- [OpenAI](https://openai.com/) – language model  
- [Google Sheets](https://www.google.com/sheets/about/) – CRM & reservation log  
- [Meta WhatsApp Business API](https://developers.facebook.com/docs/whatsapp) – customer communication  

---

## ScreenShots of Workflow
<img width="1000" height="415" alt="image" src="https://github.com/user-attachments/assets/9595620c-068e-4a05-90f8-36e776c22a6b" />
<img width="986" height="372" alt="image" src="https://github.com/user-attachments/assets/b3c23551-0cd4-49fa-afc5-62e251e929af" />


---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/restaurant-reservation-automation.git
cd restaurant-reservation-automation
```

---

### 2. Import Workflow into n8n
Open your local or cloud n8n instance.  

Go to **Workflows → Import**.  

Upload the JSON file from this repo.  

---

### 3. Configure Environment Variables
Set up your `.env` file with:

```env
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your_api_key_here
WHATSAPP_PHONE_NUMBER_ID=your_number_id
GOOGLE_SHEETS_DOC_ID=your_doc_id
OPENAI_API_KEY=your_openai_key
```

---

### 4. Run n8n:

```env
npx n8n
```

---

### 📊 Workflow Diagram

<img width="3036" height="1940" alt="WhatsApp Reservation" src="https://github.com/user-attachments/assets/775fb309-9cf6-474c-a528-1d12612239bf" />

---

### Example Usage

- Customer sends “A” → AI asks for reservation details.
- Customer sends “C” → AI calculates discount based on card choice.
- Reservation is logged in Google Sheets with status Pending or Paid.
- Customer receives WhatsApp confirmation.
