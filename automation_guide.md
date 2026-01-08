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
          python-version: '3.12'

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
Create a file at `landing/scripts/generate_blog.py`. This script handles the AI interaction, file updates, and manages the `blogs.json` data file.

```python
import os
import json
import re
import random
from datetime import datetime
import google.generativeai as genai

# Configuration - All paths are relative to the landing/ directory
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PROMPT_FILE = "prompt.txt"
BLOG_DIR = "blog"
BLOGS_JSON = "blogs.json"
SITEMAP = "sitemap.xml"
TEMPLATE_FILE = "blog/affordable-loyalty-software-for-small-business-boost-customer-retention.html"

def generate_blog():
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found.")
        return

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Read files with explicit encoding
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_instructions = f.read()

    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Extract layout from template
    header_parts = template_content.split('<section class="about">')
    footer_parts = template_content.split('</ul>\n            </div>\n        </div>\n    </section>')
    
    header_template = header_parts[0] + '<section class="about">\n        <div class="about-content">'
    footer_template = '\n            <div class="article-body">\n                <h3>Related articles</h3>\n                <ul>\n' + footer_parts[1]

    prompt = f"""
    Use these instructions: {prompt_instructions}
    
    Format the output as a JSON object with these keys:
    - title: String (The blog title)
    - description: String (Meta description for SEO)
    - content_html: String (The HTML content to go inside .article-body, use <h2>, <p>, <ul>, <li>)
    - category: String (One of: 'Customer Loyalty', 'Business Strategy', 'Coffee Shops', 'Seasonal Sales', 'Loyalty Programs', 'Customer Retention')
    - excerpt: String (A 1-2 sentence summary for the blog card)
    - slug: String (URL friendly version of title, e.g., 'how-to-boost-sales')

    Ensure the tone is encouraging and practical for small business owners. Return ONLY the JSON.
    """

    response = model.generate_content(prompt)
    try:
        json_str = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_str)
    except Exception as e:
        print(f"Failed to parse AI response: {e}")
        return

    # 1. Create the new HTML file
    new_filename = f"{data['slug']}.html"
    file_path = os.path.join(BLOG_DIR, new_filename)
    
    page_html = header_template
    page_html = re.sub(r'<title>.*?</title>', f"<title>{{data['title']}} | StampCircle</title>", page_html)
    page_html = re.sub(r'<meta name="title" content=".*?">', f'<meta name="title" content="{{data["title"]}}">', page_html)
    page_html = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{{data["description"]}}">', page_html)
    
    page_html += f'\n            <h1 class="section-title">{{data["title"]}}</h1>'
    page_html += '\n            <p style="opacity: 0.9; margin-bottom: 3rem; font-size: 1.1rem;">⏱️ 5 min read</p>'
    page_html += f'\n            <div class="article-body">\n{{data["content_html"]}}\n'
    page_html += footer_template

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(page_html)
    print(f"Created new blog: {{file_path}}")

    # 2. Update blogs.json (Add to beginning of list)
    new_post = {
        "title": data["title"],
        "href": f"blog/{{new_filename}}",
        "category": data["category"],
        "excerpt": data["excerpt"]
    }

    try:
        with open(BLOGS_JSON, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    except Exception:
        posts = []

    posts.insert(0, new_post)

    with open(BLOGS_JSON, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4)
    print("Updated blogs.json")

    # 3. Update sitemap.xml
```

---

## Step 3: Verification
1. Push these changes to your repository.
2. Go to the **Actions** tab in GitHub.
3. Select **Daily Blog Generation** and click **Run workflow** to test it immediately.
4. Verify that:
   - A new file appears in `landing/blog/`.
   - `landing/blogs.json` has a new entry at the top of the list.
   - `landing/blogs.html` dynamically fetches and displays the new post.
   - `landing/sitemap.xml` includes the new URL.
