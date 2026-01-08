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
from google import genai
from google.genai import types

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

    client = genai.Client(api_key=GEMINI_API_KEY)
    model_id = "gemini-2.0-flash-exp"

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
    
    Target Audience: Philippine small business owners (SMEs), coffee shop owners, retail managers, and service providers (salons, spas) looking to improve sales and customer retention.
    
    SEO Goals:
    - Primary Keywords: 'how to increase sales for small business Philippines', 'digital stamp cards Philippines', 'customer loyalty program Philippines', 'business promotion ideas Philippines', 'improve repeat customers'.
    - Tone: Practical, encouraging, and localized for the Philippine market (mentioning local business contexts like 'ber months', 'sari-sari stores', 'local cafes', etc., where appropriate).
    
    Format the output as a JSON object with these keys:
    - title: String (SEO-friendly title using high-volume keywords, e.g., '5 Ways to Increase Your Cafe Sales in the Philippines with Digital Stamp Cards')
    - description: String (SEO meta description, max 160 chars, includes call to action)
    - content_html: String (The HTML content to go inside .article-body. Use <h2> for subheadings, <p> for paragraphs, and <ul>/<li> for lists. Naturally integrate keywords.)
    - category: String (One of: 'Customer Loyalty', 'Business Strategy', 'Coffee Shops', 'Seasonal Sales', 'Loyalty Programs', 'Customer Retention')
    - excerpt: String (A 1-2 sentence summary for the blog card, includes primary keywords)
    - slug: String (SEO-friendly URL slug, e.g., 'increase-sales-small-business-philippines-loyalty')
    - social_poster_text: String (Text for social media poster)
    - social_caption: String (Caption for social media including relevant hashtags like #SMEPhilippines #StampCircle #CustomerLoyalty)

    Return ONLY the JSON.
    """

    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
        ),
    )
    
    try:
        data = json.loads(response.text)
    except Exception as e:
        print(f"Failed to parse AI response: {e}")
        return

    # 1. Create the new HTML file
    new_filename = f"{data['slug']}.html"
    file_path = os.path.join(BLOG_DIR, new_filename)
    
    # Calculate accurate reading time (average 200 words per minute)
    word_count = len(re.findall(r'\w+', data['content_html']))
    read_time = max(1, round(word_count / 200))

    page_html = header_template
    page_html = re.sub(r'<title>.*?</title>', f"<title>{{data['title']}} | StampCircle</title>", page_html)
    page_html = re.sub(r'<meta name="title" content=".*?">', f'<meta name="title" content="{{data["title"]}}">', page_html)
    page_html = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{{data["description"]}}">', page_html)
    
    page_html += f'\n            <h1 class="section-title">{{data["title"]}}</h1>'
    page_html += f'\n            <p style="opacity: 0.9; margin-bottom: 3rem; font-size: 1.1rem;">⏱️ {{read_time}} min read</p>'
    page_html += f'\n            <div class="article-body">\n{{data["content_html"]}}\n'
    
    # Add Social Media Footnote
    page_html += f"""
                <hr style="margin: 3rem 0 2rem; border: 0; border-top: 1px solid rgba(255,255,255,0.2);">
                <div class="social-footnote" style="font-size: 0.85rem; opacity: 0.8; line-height: 1.4;">
                    <p><strong>Social Media Poster Text:</strong><br>{{data.get('social_poster_text', '')}}</p>
                    <p style="margin-top: 1rem;"><strong>Social Media Caption:</strong><br>{{data.get('social_caption', '')}}</p>
                </div>
    """
    
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
