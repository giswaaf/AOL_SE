
# 🤝 Contributing to Smart Attendance

Thanks for contributing to **Smart Attendance** 🎓  
This guide explains how to contribute cleanly and efficiently.

Please follow the [Code of Conduct](https://github.com/nem-web/smart-attendance/blob/main/CODE_OF_CONDUCT.md).


## 🧰 Prerequisites

Before you begin, make sure you have the following installed:
- [Python](https://www.python.org/) (v3.10 or higher) - Required for backend-api and ml-service
- [Node.js](https://nodejs.org/) (v18 or higher) - Required for frontend only
- [Git](https://git-scm.com/)
- [MongoDB](https://www.mongodb.com/try/download/community) (v5.0 or higher) - For data storage

---


## 🚀 Your First Contribution (Step-by-Step)

1. **Find an Issue**
   - Look for issues tagged `good first issue` or `beginner friendly`.
   - Comment _"Hi! I'd like to work on this issue. Please assign it to me."_  
   ✅ Only comment if the issue is unassigned.

2. **Fork the Repo**

```bash
# In your browser
Click the "Fork" button in the top-right of the repo
```

3. **Clone Your Fork**

```bash
git clone https://github.com/YOUR-USERNAME/smart-attendance.git
cd smart-attendance
```

4. **Local Development Setup**

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

#### Backend API Setup

```bash
cd server/backend-api

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and configure (see README.md for details)
cp .env.example .env

# Run the backend API
python -m app.main
```

The backend API will be available at `http://localhost:8000`

#### ML Service Setup

```bash
cd server/ml-service

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and configure (see README.md for details)
cp .env.example .env

# Run the ML service
python -m app.main
```

The ML service will be available at `http://localhost:8001`

5. **Create a Branch**

```bash
git checkout -b fix-typo-homepage
```

6. **Make Your Changes**
- Keep components small and readable
- Follow existing patterns (don’t freestyle)
- Use Tailwind utilities instead of random CSS
- Don’t hardcode colors — use CSS variables

7. **Lint, Build, Commit**

**For Frontend:**
```bash
cd frontend
npm run lint
npm run build
git add .
git commit -m "Improve: dashboard card spacing"
git push origin feature/improve-dashboard-ui
```

**For Backend Services (Python):**
```bash
# Python linting is optional - follow existing code style
git add .
git commit -m "Fix: attendance API endpoint"
git push origin feature/fix-attendance-api
```

If lint fails → fix it. No shortcuts.

8. **Create a Pull Request**
- Explain what you changed
- Explain why
- Add screenshots for UI changes
- Link the issue (if any)


9. **Keep Fork Updated**

```
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

---

## ✅ Contribution Rules

- 🔹 Work on only one issue at a time
- 🔹 Wait to be **assigned** before working on an issue
- 🔹 Write **clear commit messages** (`Type: Description`)
- 🔹 Test your changes thoroughly before creating a PR
- 🔹 Be respectful and inclusive in all discussions
- 🔹 Use screenshots for UI-related PRs

---

## 📌 Pull Request Checklist

Use this PR template when submitting:

```md
## What I Changed
- [Explain what you did]

## Why It Was Needed
- [Reason behind the change]

## How to Test
1. Go to...
2. Perform...
3. You should see...

## Screenshots (if applicable)
![before](url) ![after](url)

Fixes #<issue-number>
```

✅ PR Title Examples:
- `Fix: Navbar menu not opening on mobile`
- `Add: New badge system for users`
- `Update: README with better setup guide`

---

## 🐞 Creating & Reporting Issues

### Bug Report Template

```md
## Bug Description
[What’s broken?]

## Steps to Reproduce
1. Go to...
2. Click on...
3. Observe...

## Expected Behavior
[What should happen?]

## Screenshots
[Add if helpful]

## System Info
- OS: [Windows/Mac/Linux]
- Browser: [Chrome/Firefox/Safari]
```

### Feature Request Template

```md
## Feature Description
[What you want to add]

## Why It's Useful
[How it helps users]

## Possible Implementation
[Ideas for how it might work]
```


## 🆘 Need Help?

- Check out the [learn.md](./learn.md) file for detailed Git and GitHub tutorials
- Open a discussion in the Issues tab
- Reach out to maintainers

## ✅ Code Review Process

1. A maintainer will review your PR
2. They may request changes or ask questions
3. Make requested changes and push updates
4. Once approved, your PR will be merged
5. Congratulations! 🎉 You're now a contributor!

## 🏆 Recognition

All contributors will be recognized in our project. Your contributions, no matter how small, are valued and appreciated!

## 📜 License

By contributing to Smart Attendance, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Smart Attendance! Together, we're building something amazing! 🚀
