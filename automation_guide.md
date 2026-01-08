# Automation Guide: Daily AI Blog Generation

This guide outlines how to set up a GitHub Action to automatically generate and publish blog posts using Gemini AI every day at 11:00 AM and 5:00 PM PHT.

## Prerequisites
1. **Gemini API Key**: Obtain one from the [Google AI Studio](https://aistudio.google.com/).
2. **GitHub Secret**: Add your API key to your repository:
   - Go to **Settings > Secrets and variables > Actions**.
   - Create a new repository secret named `GEMINI_API_KEY`.
3. **Workflow Permissions**:
   - Go to **Settings > Actions > General**.
   - Under **Workflow permissions**, select **Read and write permissions**.

---

## Step 1: Create the GitHub Action Workflow
Create a file at `.github/workflows/daily_blog.yml`:

```yaml
name: Daily Blog Generation

on:
  schedule:
    - cron: '0 3 * * *' # 11:00 AM PHT (UTC+8)
    - cron: '0 9 * * *' # 5:00 PM PHT (UTC+8)
  workflow_dispatch:

jobs:
  generate-blog:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install google-generativeai

      - name: Run generation script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python scripts/generate_blog.py

      - name: Commit and push changes
        run: |
          git config --global user.name "GitHub Action"
          git config --global user.email "action@github.com"
          git add landing/blog/*.html landing/blogs.html landing/sitemap.xml
          git commit -m "docs: auto-generate daily blog post" || echo "No changes to commit"
          git push
```

---

## Step 2: Create the Python Script
Create a file at `scripts/generate_blog.py`. This script handles the AI interaction and file updates.

```python
import os
import random
import re
from datetime import datetime
import google.generativeai as genai

# Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PROMPT_FILE = "landing/prompt.txt"
BLOG_DIR = "landing/blog"
BLOGS_HTML = "landing/blogs.html"
SITEMAP = "landing/sitemap.xml"
TEMPLATE_FILE = "landing/blog/affordable-loyalty-software-for-small-business-boost-customer-retention.html"

def generate_blog():
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')

    with open(PROMPT_FILE, 'r') as f:
        prompt_text = f.read()

    # Request AI to generate content based on prompt and template structure
    response = model.generate_content(f"""
    Use the instructions in this prompt: {prompt_text}
    
    Convert the result into a full HTML article following the exact styling and structure of this file:
    (Provide the content of {TEMPLATE_FILE} as context here)
    
    Return the response in JSON format with:
    - title: The blog title
    - description: Meta description
    - content: The full HTML body (content inside .article-body)
    - category: One of 'Customer Loyalty', 'Business Strategy', 'Coffee Shops', 'Seasonal Sales', 'Loyalty Programs', 'Customer Retention'
    - excerpt: A short summary for the blog card
    """)
    
    # Parse AI response and write to files...
    # (Implementation details for parsing and file manipulation)

if __name__ == "__main__":
    generate_blog()
```

---

## Step 3: Verification
1. Push these changes to your repository.
2. Go to the **Actions** tab in GitHub.
3. Select **Daily Blog Generation** and click **Run workflow** to test it immediately.
4. Verify that:
   - A new file appears in `landing/blog/`.
   - `landing/blogs.html` has a new entry in the `posts` array.
   - `landing/sitemap.xml` includes the new URL.
