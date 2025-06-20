# 🚀 How To Set Up A Remote MCP Client Server on Render.com For Anthropic and OpenAI Agents🚀

---
**Hello!**

This notebook is a practical guide for deploying your own Model Context Protocol (MCP) server **remotely**, using free cloud hosting on [Render](https://render.com).

Unlike most MCP examples - which focus on running a server on your own computer to use with tools like Claude Desktop — this guide shows you how to host your MCP server in the cloud, making it accessible from anywhere and easy to integrate into web agents, chatbots, or even share with others.

At the end I'll also show you how to connect this up to the **Claude web UI** and **OpenAI playground**.

**LINK TO THE COLAB: 
**
[https://colab.research.google.com/github/smartaces/render_mcp/blob/main/How_To_Set_Up_A_Remote_MCP_Client_Server_on_Render_For_Anthropic_and_OpenAI_Agents.ipynb](https://github.com/smartaces/render_mcp/blob/main/How_To_Set_Up_A_Remote_MCP_Client_Server_on_Render_For_Anthropic_and_OpenAI_Agents.ipynb)

---

![image](https://github.com/user-attachments/assets/ed77afdc-3be5-40db-87b6-9dfb78ef3058)

#**Connect with Me** 👋

If you like this notebook or in any way found it helpful, feel free to connect with me on LinkedIn here:

https://www.linkedin.com/in/jamesbentleyai/

---

---
## What is MCP?

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/introduction) is an open standard developed by Anthropic to connect AI models to external tools, data sources, and workflows.

Some people describe MCP as a “USB-C” port for AI—providing a common protocol so applications can plug into tools, access data from sources like GitHub or Google Docs, and extend their abilities without custom, one-off integrations.

MCP uses a simple client-server architecture:

- **Client**: Runs inside your AI app (like Claude, an IDE, or a chatbot).
- **Server**: Exposes tools, resources, and prompt templates to the client.
- This server can be local or, as you’ll learn here, remote and cloud-hosted!

You can find more about MCP here:

🔗 [MCP Introduction](https://modelcontextprotocol.io/introduction)  
🔗 [Official MCP Servers on GitHub](https://github.com/modelcontextprotocol/servers)

---

## How is this notebook different?

- **Remote-first:** Instead of local desktop hosting, you’ll deploy your server to Render’s free cloud platform.

- **Reusable:** The steps you’ll follow can be applied to deploy any kind of server remotely, not just MCP.

- **Bugfix included:** If you’ve taken the [DeepLearning.AI MCP course](https://www.deeplearning.ai/short-courses/mcp-build-rich-context-ai-apps-with-anthropic/), you may have encountered a minor issue deploying the Arxiv agent remotely. This notebook includes a fix, so your deployment works out of the box. In doing so this notebook works as an addendum to the official DeepLearning.AI course, but is also fully self-contained.

---

## What will you learn?

- How MCP standardizes connecting AI models to external tools and data
- How to clone and deploy an MCP server on Render
- How to fix issues with the Arxiv agent’s remote deployment
- **How to use both Anthropic (Sonnet 4) and OpenAI (GPT-4.1) models to talk to your MCP server via chat agents**
---

Ready to get started? Let’s deploy your own remote MCP server!
