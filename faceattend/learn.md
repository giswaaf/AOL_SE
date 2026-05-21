# 📘 Smart Attendance Contributor Guide

Welcome to **Smart Attendance 🎓**
This guide is your practical roadmap to learn the codebase, understand the stack, and contribute without breaking things.

> _"Every expert was once a beginner. Don’t be afraid to start small!"_

---

## 🧭 Table of Contents

- [🆕 New to Git & GitHub? Start Here](#-new-to-git--github-start-here)
- [⚛️ Understanding This Project](#️-understanding-this-project)
- [🚀 Your First Contribution: Step-by-Step](#-your-first-contribution-step-by-step)
- [🆘 FAQs & Help](#-faqs--help)
- [🏁 Final Tips](#-final-tips)

---

## 🆕 New to Git & GitHub? Start Here

### Prerequisites

1. Create a GitHub account: [github.com](https://github.com)
2. Install Git: [git-scm.com](https://git-scm.com)
3. For frontend development: Node.js 18+ and npm 9+
4. For backend development: Python 3.10+ and pip
5. For database: MongoDB 5.0+
6. Configure Git (in terminal):

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## ⚛️ Understanding This Project

This repository contains a full-stack Smart Attendance System with three main components:

### Project Structure
- **Frontend** - React-based web application for user interface
- **Backend API** - FastAPI service handling authentication, user management, and business logic
- **ML Service** - FastAPI service with facial recognition capabilities using MediaPipe and OpenCV

### What this system does?
- Teacher login & authentication UI
- Dashboard with attendance analytics
- Webcam-based attendance capture using facial recognition
- Student list with attendance percentage tracking
- Multi-theme UI (Light / Dark / Soft)
- Real-time attendance marking and reporting

### Tech Stack You'll Touch

**Frontend:**
- React 19 + Vite → UI & routing
- Tailwind CSS v4 → Styling
- CSS Variables → Theme system
- react-webcam → Camera access
- Axios → Backend communication
- Material-UI → UI components
- Recharts → Data visualization

**Backend API:**
- FastAPI → High-performance web framework
- MongoDB + Motor → Database & async driver
- PyJWT + Authlib → Authentication
- Cloudinary → Image storage
- Passlib → Password hashing

**ML Service:**
- FastAPI → Web framework
- MediaPipe → Face detection
- OpenCV → Image processing
- NumPy → Numerical operations
- Pillow → Image handling

If you know basic React + CSS for frontend work, or Python + FastAPI for backend services, you're good to go.


## 🏁 Final Tips

- 🎯 Start small: Even fixing a typo counts!
- 🧠 Learn by reading others’ code and PRs
- 🧼 Keep your branches clean and organized
- 🫱🏽‍🫲🏾 Ask for help when stuck — we’re here for you!
- 🎉 Most importantly: **Have fun while learning and building!**

---

Let’s build something amazing together at **Smart Attendance** ✨
